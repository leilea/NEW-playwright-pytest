## 上下文

当前系统中步骤数据存在两种格式：

| 格式 | 结构 | 来源 |
|------|------|------|
| 嵌套格式 | `{action: "click", params: {selector: "#btn"}}` | 后端 recorder.py 产出 |
| 展平格式 | `{action: "click", selector: "#btn"}` | 前端 RecorderPanel 处理后存入 DB |

`script_gen.py` 仅支持嵌套格式（`s.get("params", {})`），导致从 DB 读取的展平格式步骤生成空脚本。

## 目标 / 非目标

**目标：**
- `script_gen.py` 同时兼容展平格式和嵌套格式的步骤参数读取
- 不影响已有功能：脚本预览（`GET /api/cases/:id/script`）和回放（`playback.py`）
- 向后兼容：使用 `{action, params}` 格式的步骤仍正常工作
- 无需数据库迁移

**非目标：**
- 不改变步骤存储格式
- 不修改前端 RecorderPanel 或 StepEditor
- 不切换到新模式录制器（recorder_process.py）

## 决策

### 决策 1：在 `generate_script()` 中兼容展平格式

**方案**：将第 19 行 `params = s.get("params", {})` 改为 `params = s.get("params") or s`

**理由**：
- 最小改动（一行），零风险
- `s.get("params")` 返回 `None`（不存在）或空 `{}`（存在但空）时，`or s` 将步骤自身作为参数源
- 嵌套格式步骤（`params` 为非空 dict）保持不变
- 无需修改 handler 函数签名，handler 读取 `params[key]` 的方式完全兼容展平格式（因为展平后 key 已在顶层 `s` 中）

**替代方案**：
- 方案 B：修改 RecorderPanel 不展平 → 需连带改 StepEditor，改动面大
- 方案 C：增加 normalize 中间层 → 过度设计

## 风险 / 权衡

- [风险] `params` 为合法空字典 `{}` 时被当作业缺失处理
  → 缓解：`params={}`时 `{} or s` 返回 `s`，效果等价于读空字典（因为 handler 的 `.get()` 会取默认值）
- [风险] 步骤恰好有名为 `params` 的展平字段值
  → 缓解：步骤参数中无 `params` 字段（见 `step.ts` 的 STEP_SCHEMAS），不会冲突
- [权衡] 展平格式的 `action` 键会被传入 handler params 中
  → 缓解：所有 handler 均通过具名 key 读取（如 `p["url"]`），不会消费 `action`
