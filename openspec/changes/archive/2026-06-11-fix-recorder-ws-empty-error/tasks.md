## 1. 错误诊断增强

- [x] 1.1 在 `_run_recorder` 的 `except Exception` 块中添加 `traceback.format_exc()` 和 `logging.error`
- [x] 1.2   验证诊断信息正确输出到后端日志并返回前端

## 2. 前端守卫

- [x] 2.1 在 `RecorderPanel.vue` 的 `start()` 中添加重复点击守卫，防止 WS 竞态
- [x] 2.2 在 `stop()` 中添加 readyState 检查，避免关闭已断开的连接时报错

## 3. 根因修复

- [x] 3.1 根据诊断暴露的异常类型修复根本原因
- [x] 3.2 端到端验证录制功能可用
