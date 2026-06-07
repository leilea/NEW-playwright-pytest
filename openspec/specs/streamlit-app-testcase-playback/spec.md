# streamlit-app-testcase-playback 规范

## 目的
待定 - 由归档变更 add-playback-feature 创建。归档后请更新目的。
## 需求
### 需求:用户可对录制的 Playwright 脚本触发回放

系统必须为每条已录制的用例（`testcases.json` 中 `script` 字段非空）提供"▶ 回放"入口，点击后弹出回放面板并立即开始执行该脚本。

#### 场景:列表卡片触发回放
- **当** 用户在用例列表中点击某条用例的"▶ 回放"按钮
- **那么** 系统在该卡片内展开回放面板，且默认参数下（chromium + 30s 单步超时 + headless）启动一次回放

#### 场景:详情面板触发回放
- **当** 用户在用例详情 expander 底部点击"▶ 回放"
- **那么** 系统在详情面板内启动一次回放，结果写入回放历史

### 需求:回放以独立子进程方式执行

回放必须**不污染**主 Streamlit 进程的 Playwright 资源池，必须作为独立 Python 子进程执行。

#### 场景:子进程隔离
- **当** 启动一次回放
- **那么** 系统 fork 一个新的 Python 子进程（`python -u <tmp.py>`），主进程仅通过 stdout/stderr/exit code 与子进程通信

#### 场景:超时强制清理
- **当** 回放脚本执行超过 5 分钟未结束
- **那么** 系统必须 `terminate` 并最终 `kill` 子进程，记录 `status="error"`、`error="timeout"`，并清理临时脚本

### 需求:回放脚本自动注入 Playwright 上下文

录制的脚本通常是裸 `page.goto(...)` 形式（无 import、无 page 定义），回放服务必须在执行前自动注入必要头部。

#### 场景:标准裸脚本可执行
- **当** 脚本仅包含 `page.goto(url)` / `page.fill(...)` / `page.click(...)` 等无 page 定义的语句
- **那么** 注入 `from playwright.sync_api import sync_playwright` 与 `with sync_playwright() as p: browser = p.chromium.launch(headless=True); context = browser.new_context(); page = context.new_page();` 后，脚本必须能直接运行

#### 场景:脚本显式带 expect
- **当** 脚本使用了 `expect(page.locator(...)).to_be_visible()` 同步断言
- **那么** 注入头部必须同时 `from playwright.sync_api import expect`

#### 场景:脚本已有 page 定义
- **当** 脚本开头已显式 `page = browser.new_page()` 或已导入 `sync_playwright`
- **那么** 注入不得重复定义（正则检测跳过）

### 需求:回放支持运行时参数

回放面板必须允许用户在执行前选择/调整以下参数。

#### 场景:浏览器可选
- **当** 用户在回放面板中切换浏览器下拉
- **那么** 系统可选 `chromium` / `firefox` / `webkit`，默认为 `chromium`

#### 场景:单步超时可调
- **当** 用户在回放面板中拖动超时滑块
- **那么** 范围 5s - 60s，默认 30s，注入 `page.set_default_timeout(...)` 到包装脚本

#### 场景:headless 开关
- **当** 用户取消勾选 headless
- **那么** 包装脚本必须以 `headless=False` 启动浏览器（便于本地调试）

### 需求:回放必须流式返回日志

UI 必须能实时看到脚本输出，禁止等子进程退出后才一次性返回。

#### 场景:逐行输出
- **当** 回放进行中
- **那么** 子进程 stdout/stderr 每输出一行，UI 必须立即在日志区追加显示该行

#### 场景:执行结束标记
- **当** 子进程退出
- **那么** 日志区追加 `[PLAYBACK] OK` 或 `[PLAYBACK] FAILED` 标记，且状态指示器切换到 `passed`/`failed`/`error`

### 需求:回放失败时必须自动截图

回放脚本抛异常时，必须保存当前 page 状态截图作为证据。

#### 场景:失败截图
- **当** 脚本异常退出
- **那么** 系统调用 `page.screenshot(path="screenshots/playback_<tc_id>_<ts>.png")` 保存截图，且 UI 在结果区展示该截图（若 `screenshots/` 目录下文件存在）

#### 场景:截图前 page 已死
- **当** 异常发生在 `browser.new_page()` 之前（如浏览器启动失败）
- **那么** 必须吞掉截图异常（`try/except`）并继续记录 `screenshot=null`，不掩盖主异常信息

### 需求:回放历史必须持久化

每次回放的执行记录必须写入 `logs/playback_history.json`，重启 Streamlit 后仍可查询。

#### 场景:写入记录
- **当** 一次回放结束（无论成功失败或超时）
- **那么** 系统追加一条记录 `{tc_id, ts, status, duration_ms, browser, screenshot, exit_code}` 到 `logs/playback_history.json`

#### 场景:历史查询
- **当** UI 加载用例详情页
- **那么** 系统调用 `list_playback_history(tc_id, limit=5)` 返回该用例最近 5 次记录，按时间倒序展示

#### 场景:孤儿清理
- **当** 用户保存一条新回放记录
- **那么** 系统同时调用 `cleanup_orphans(max_age_days=30)` 删除 `screenshots/playback_*.png` 中 30 天以上且历史里已无引用者

### 需求:回放必须是并发安全的

多个用户同时点击"▶ 回放"或同一用户连续点击，必须不互相污染。

#### 场景:每条用例独立临时文件
- **当** 启动一次回放
- **那么** 临时脚本名必须为 `logs/_playback_tmp_<uuid4>.py`（uuid 保证唯一），执行后立即删除

#### 场景:同 tc 并发回放
- **当** 同一用例的两次回放被同时触发
- **那么** 第二次进入回放面板时如已有进行中回放，必须禁用"开始回放"按钮（避免进程泄漏）

### 需求:回放不修改原用例数据

回放必须只读用例的 `script` 字段，禁止修改 `testcases.json`、禁止写入 allure 报告。

#### 场景:只读脚本
- **当** 启动回放
- **那么** 服务只读取 `tc["script"]` 字段，不调用 `update_testcase`

#### 场景:不污染测试报告
- **当** 启动回放
- **那么** 临时脚本禁止调用 `pytest.main` 或向 `allure-results/` 写入任何文件

