## 为什么

录制生成的测试脚本中每条操作步骤都重复出现两次。根因是 `recorder_process.py` 注入的 JS 中 `rec()` 函数同时通过 `console.log` 和 `window.__dsep_queue` 双通道发射事件，导致每条用户操作被 `handle_console()` 和 `flush_queue()` 各 emit 一次到 stdout，`rec_ws.py` 读取后全部转发给前端，最终每条指令在生成的脚本中出现两次。

## 变更内容

- 移除 `RECORDER_INJECT_JS` 中 `rec()` 函数内的 `console.log('__DSEP__' + ...)` 调用
- 移除 Python 端 `handle_console()` 函数及其 `page.on("console", ...)` 注册
- 保留 `flush_queue()` 作为唯一的事件发射路径

## 功能 (Capabilities)

### 新增功能
无

### 修改功能
- `case-recording`: 修复录制过程中步骤事件双重发射导致脚本重复的问题

## 影响

- `backend/app/services/recorder_process.py` — 移除 console.log 调用和 handle_console 函数
- 无 API 变更，无 Breaking 变更
