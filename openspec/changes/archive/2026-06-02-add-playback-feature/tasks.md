## 1. 持久化层（playback_history）

- [x] 1.1 创建 `streamlit_app/utils/playback_history.py`，实现 4 个函数：`load_all()` / `list_for_tc(tc_id, limit)` / `save_record(...)` / `cleanup_orphans(max_age_days)`
- [x] 1.2 实现 `save_record` 的原子写（临时文件 + `os.replace`）
- [x] 1.3 在 `playback_history.py` 顶部加启动时一次性的孤儿清理（删除 `logs/_playback_tmp_*.py` 中 > 1h 的）

## 2. 核心服务（playback_service）

- [x] 2.1 创建 `streamlit_app/services/playback_service.py`，定义 `DEFAULT_TIMEOUT_MS = 30_000` / `MAX_TIMEOUT_S = 300` 常量
- [x] 2.2 实现 `_wrap_script(script_text, browser, headless, timeout_ms) -> str`：注入 prelude + 8 空格缩进用户脚本 + epilogue；正则检测跳过已存在的 import / page 定义
- [x] 2.3 实现 `playback_stream(tc, browser, headless, timeout_ms) -> Generator[str, None, dict]`：写临时文件 + Popen 子进程 + reader thread + queue + 流式 yield + 最终 return 结果 dict
- [x] 2.4 实现 `stop_playback(handle) -> None`：terminate / kill 子进程
- [x] 2.5 在子进程退出后解析日志中的 `SCREENSHOT=...` 标记，回填到结果 dict

## 3. 用例服务扩展（testcase_service）

- [x] 3.1 在 `streamlit_app/services/testcase_service.py` 末尾新增 `list_playback_history(tc_id, limit=5)` 转发函数

## 4. UI 改造（page_testcases）

- [x] 4.1 在 `streamlit_app/page_testcases.py` 顶部 session_state 初始化中追加 `tc_playback_running` / `tc_playback_handle` / `tc_playback_logs` / `tc_playback_result` 四个键
- [x] 4.2 改造列表卡片按钮区为 4 列（查看/▶/编辑/删除），并显示回放状态徽标（折叠时）
- [x] 4.3 实现 `_render_playback_panel(tc, in_detail)` 内部函数：参数表单（浏览器 selectbox / 超时 slider / headless checkbox）+ 按钮组 + `st.code` 日志流 + 结果区（截图）+ 最近 5 次历史表
- [x] 4.4 详情 expander 末尾追加"🎬 回放历史"小节
- [x] 4.5 处理并发态：同一 tc 已有进行中回放时禁用"开始"按钮

## 5. 冒烟测试

- [x] 5.1 录制脚本回放服务核心已通过端到端测试（_wrap_script 6 单元用例 + playback_stream 2 真实子进程用例）
- [x] 5.2 默认参数下回放通过（Test A: example.com, status=passed, 3.6s, exit=0）
- [x] 5.3 选择器错误时回放失败（Test B: #nonexistent, status=failed, 4.9s, exit=1, 完整 traceback）
- [x] 5.4 Streamlit AppTest 验证 page_testcases.py 无加载异常
- [x] 5.5 `logs/playback_history.json` 已存在且 JSON 合法（含 E2E 写入的 tc_pass_e2e / tc_fail_e2e 两条记录）

## 6. 文档与归档

- [x] 6.1 运行 `openspec-cn validate add-playback-feature` 确认无 schema 错误
- [x] 6.2 运行 `openspec-cn archive add-playback-feature` 归档变更
- [x] 6.3 验证 `openspec/specs/streamlit-app-testcase-playback/spec.md` 已落到主规范目录
