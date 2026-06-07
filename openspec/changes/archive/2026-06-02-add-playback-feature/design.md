# 设计：录制脚本回放功能

## 上下文

- **当前状态**：`streamlit_app/services/testcase_service.py` 提供用例 CRUD，`logs/testcases.json` 持久化 `script` 字段（录制的裸 Playwright Python 同步脚本）。`streamlit_app/utils/test_executor.py` 用 `subprocess.Popen` + `threading + queue` 模式实现 pytest 流式输出（已有成熟范式可参考）。
- **约束**：
  - 不能改 `tests/`、`conftest.py`、`pytest.ini`
  - 不能引入新依赖
  - 子进程必须与 Streamlit 主进程隔离（独立 Playwright 资源池）
  - 临时文件必须可清理（5 分钟超时 + uuid 命名）
- **利益相关者**：QA 工程师（核心用户）、平台维护者（不希望回归）

## 目标 / 非目标

**目标**：
- 在 UI 中提供"点一下就能跑"的回放能力
- 失败时自动留证（截图 + 历史）
- 子进程隔离，不污染主进程

**非目标**：
- 不做视频录制
- 不做 baseline 截图对比
- 不做录制/回放 diff
- 不修前序报告的 5 个既有 bug
- 不修改 `testcase.json` 数据结构

## 决策

### 决策 1：独立子进程 + 同步 Playwright API

**采用**：回放服务把 `tc["script"]` 包成独立 .py 文件，用 `subprocess.Popen([sys.executable, "-u", tmp_path], ...)` 启动新进程，调用 `playwright.sync_api`。

**理由**：
- Playwright 浏览器进程是强独占资源，**同进程内并发 2 个浏览器实例**会引发 "Chromium instance is already running" 错误
- 子进程模式与现有 `test_executor.py` 一致，团队熟悉
- 失败时主进程不受影响

**替代方案**：
- ❌ 同进程 threading：Playwright sync API 与 thread 不友好，需要每个 thread 独立 sync_playwright() 实例，复杂度高且易出资源竞争
- ❌ 复用 pytest 子进程：录制的脚本不是 pytest 格式，包成 pytest 启动成本高、依赖 fixture 链路

### 决策 2：脚本自动注入而非用户改写

**采用**：`_wrap_script(script_text)` 在执行前注入头部，**不修改** `tc["script"]`。

**理由**：
- 录制的脚本是只读资产，多次回放不能累积副作用
- 自动注入的逻辑收敛在服务层一处，便于升级

**注入策略**（简化版）：
```python
PRELUDE = """
import sys, traceback, time
from playwright.sync_api import sync_playwright
err_screenshot = None
try:
    with sync_playwright() as p:
        browser = p.{browser}.launch(headless={headless})
        context = browser.new_context()
        page = context.new_page()
        page.set_default_timeout({timeout_ms})
        # === USER SCRIPT BELOW ===
"""
EPILOGUE = """
        # === USER SCRIPT ABOVE ===
        context.close()
        browser.close()
        print("[PLAYBACK] OK")
except Exception as e:
    ts = int(time.time())
    err_path = f"screenshots/playback_err_{ts}.png"
    try:
        page.screenshot(path=err_path)
        err_screenshot = err_path
    except Exception:
        pass
    traceback.print_exc()
    print(f"[PLAYBACK] FAILED;SCREENSHOT={err_screenshot or 'none'}")
    sys.exit(1)
"""
```

中间的用户脚本按 8 空格缩进包裹（因为嵌套在 `try:` 块内多两层）。

**正则检测**跳过：
- 已 `from playwright.sync_api import`
- 已 `import playwright`
- 已定义 `page =`

### 决策 3：流式日志靠 threading + queue（沿用 test_executor 模式）

**采用**：在 Streamlit 主线程外启 `daemon=True` 的 reader thread 持续 `proc.stdout.readline()`，把每行塞进 `queue.Queue()`，主线程在 `playback_stream` 生成器里 `queue.get(timeout=0.1)` yield。

**理由**：与 `test_executor.py` 完全一致的范式，代码风格统一，团队心智负担低。

**特殊处理**：
- `python -u` 强制无缓冲输出
- `queue.get(timeout=0.1)` 短轮询避免死锁
- `proc.wait(timeout=...)` 配合 `MAX_TIMEOUT_S=300` 强制超时

### 决策 4：历史记录 JSON 文件（非 SQLite）

**采用**：`logs/playback_history.json` 用 `json.dump(indent=2)` 持久化。

**理由**：
- 与 `testcases.json` / `trends.json` 风格一致
- 当前用例库量级（< 1000 条）+ 每次回放 1 条记录，文件读写压力极小
- 人类可读，便于排查

**性能与并发**：
- 读用 `json.load` 一次性全量加载（< 1ms）
- 写用临时文件 + 原子 `os.replace`（防半写）
- 不加锁（单用户本地工具；如需可后续加 `fcntl`）

### 决策 5：UI 用 `st.expander` 内嵌（非 `st.dialog`）

**采用**：回放面板作为卡片内的可折叠 expander。

**理由**：
- 现有 `page_testcases.py` 列表/详情都用 `st.expander` 模式，保持视觉一致
- 避免 `st.dialog` 的阻塞性（用户不能同时操作其它用例）
- 一目了然看到所有用例的回放状态徽标

**状态徽标逻辑**（折叠时显示）：
- 有历史且最近一次 passed → 🟢
- 有历史且最近一次 failed → 🔴
- 有历史且最近一次 error → ⚠️
- 无历史 → ⚪ 未回放

### 决策 6：超时 5 分钟 + uuid 临时文件名

**采用**：`MAX_TIMEOUT_S = 300`，临时文件 `logs/_playback_tmp_<uuid4>.py`。

**理由**：
- 单条录制脚本合理时长 < 2 分钟；5 分钟给特殊场景留余量
- uuid4 保证并发不冲突
- 启动时扫一次 `logs/_playback_tmp_*.py`，删除超过 1 小时的孤儿

## 风险 / 权衡

- **[风险] 录制的脚本语法错误** → 缓解：注入头部后做一次 `compile()` 校验，失败时 UI 直接显示 SyntaxError 不启动子进程
- **[风险] 浏览器二进制未安装**（如未 `playwright install firefox`） → 缓解：捕获 `playwright._impl._errors.Error`，UI 提示 "请先运行 `playwright install <browser>`"
- **[风险] 截图目录膨胀** → 缓解：`cleanup_orphans(max_age_days=30)` 在 `save_record` 时同步清理
- **[风险] 临时文件残留**（机器断电等） → 缓解：每次 `playback_stream` 启动时扫一次 `logs/_playback_tmp_*.py` 删除 1h 前的
- **[权衡] 子进程冷启动 ~1-2s** → 接受：单次回放用户预期是 5-30s 级别，启动开销占比 < 5%
- **[权衡] 不做视频录制** → 接受：失败截图 + 日志已足够定位，可后续扩展

## 迁移计划

无破坏性变更，**不需迁移**：
- 新增文件不影响既有路径
- 既有用例数据无需迁移
- 启动后立即可用，无需手动初始化

## 开放问题

- 无（已与用户确认所有关键决策）
