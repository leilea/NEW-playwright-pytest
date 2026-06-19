## 为什么

录制生成的测试用例步骤在保存到数据库后，脚本生成器和回放引擎无法正确读取步骤参数，导致脚本预览为空参数、回放必然失败。根因是步骤数据格式在传输链路上发生了不一致：后端以 `{action, params: {...}}` 发送，前端展平为 `{action, url:"...", selector:"..."}` 后存入数据库，但 `script_gen.py` 仍按 `s.get("params")` 读取——始终读到空对象。

## 变更内容

- 修改 `backend/app/services/script_gen.py`，使步骤参数读取兼容展平格式：当 `params` 键不存在时，将步骤自身视为参数源
- 向后兼容旧的嵌套 `params` 格式

## 功能 (Capabilities)

### 新增功能
（无）

### 修改功能
- **case-recording**: 录制完成后生成的 pytest 脚本必须正确解析展平格式的步骤参数，脚本预览和回放均正确执行
- **case-playback**: 回放引擎生成的 pytest 脚本必须正确包含所有步骤参数（URL、选择器、值等）

## 影响

- `backend/app/services/script_gen.py` — 步骤参数解析逻辑
- `GET /api/cases/{id}/script` — 脚本预览接口（间接修复）
- `backend/app/services/playback.py` → `run_playback()` — 回放功能（间接修复）
- 数据库现有数据不受影响，无需迁移
