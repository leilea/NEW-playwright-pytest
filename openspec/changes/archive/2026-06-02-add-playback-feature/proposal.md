## 为什么

当前通过 `streamlit_app` 录制的 Playwright 脚本保存在 `logs/testcases.json` 中，但**没有任何机制验证脚本是否可执行**。QA 工程师录制完成后只能：
1. 复制到 IDE 手动跑（脱离平台，体验断裂）
2. 推到 pytest 走完整 fixture 链路（启动慢、依赖多、不必要）

缺乏"在录制/编辑/保存的当下点一下就能回放验证"的能力，使得用例库中积攒大量"录制过但跑不通"的死脚本，污染资产。

## 变更内容

为 Streamlit 用例管理页面新增 **录制脚本回放（Playback）** 能力：

- **新增** `streamlit_app/services/playback_service.py`：把用例的 `script` 字段包装成可执行 Playwright Python 脚本，通过独立子进程运行，**流式返回日志**，**失败时自动截图**。
- **新增** `streamlit_app/utils/playback_history.py`：把每次回放记录持久化到 `logs/playback_history.json`。
- **新增** 用例规约 `streamlit-app-testcase-playback`：定义回放的接口契约与数据契约。
- **扩展** `streamlit_app/services/testcase_service.py`：新增 `list_playback_history(tc_id, limit)` 转发函数。
- **修改** `streamlit_app/page_testcases.py`：列表卡片 4 列按钮（查看/▶ 回放/编辑/删除）+ 卡片内嵌回放面板（参数+日志流+结果+历史）+ 详情页底部追加"回放历史"小节。

**不涉及**：
- 不修改 `conftest.py`、不修改 `tests/`、不修改 `pytest.ini`
- 不修改任何已存在的测试用例数据
- 不修复先前报告的 5 个既有 bug（`import time` 缺失、`pytest.unique_id`、`recording_service` 签名等）—— 保持单一职责
- 不引入新依赖（用项目已有的 `playwright`、`subprocess`、`streamlit`）

## 功能 (Capabilities)

### 新增功能
- `streamlit-app-testcase-playback`: 用例回放能力 —— 把录制的 Playwright 脚本作为独立子进程执行，验证可执行性、实时反馈日志、失败时截图、保留历史

### 修改功能
- 无（既有 `testcase-service` 规范若存在也仅是增加新方法，不改契约）

## 影响

- **代码**：`streamlit_app/` 子树新增 2 文件 + 修改 2 文件
- **数据**：新增 `logs/playback_history.json`（启动时自动创建）+ `screenshots/playback_*.png` 截图
- **运行时**：每次回放会启动一个临时 Python 子进程 + 1 个 headless 浏览器实例（5 分钟超时强制清理）
- **依赖**：无新增
- **测试代码**：无影响
