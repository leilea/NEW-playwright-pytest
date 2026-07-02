## 上下文

当前回放执行通过 `playback.py` 的 `run_playback()` 起 pytest 子进程，返回原始 stdout/stderr。前端 `CaseEditor.vue` 直接展示这些文本，用户需要自行从堆栈中提取关键错误信息。

**现状：**
- 后端返回：`{status, stdout, stderr, rc, screenshot}`
- 前端展示：el-alert（通过/失败）+ raw stdout + raw stderr
- 错误信息埋在 stderr 和 stdout 末尾的 pytest 堆栈中

**目标：** 解析 Playwright 错误模式，前端以结构化中文方式展示。

## 目标 / 非目标

**目标：**
- 后端解析 pytest 输出，提取结构化错误信息
- 前端展示中文错误提示：哪个定位器、什么错误类型、在第几步
- 保留原始 stdout/stderr 可折叠查看

**非目标：**
- 不修改脚本生成逻辑（script_gen.py）
- 不修改 WebSocket 协议结构（playback_ws.py）
- 不引入 i18n 框架
- 不做步骤级逐行回放进度流

## 决策

### 决策 1：后端解析 vs 前端解析
**选择：后端解析**（在 `playback.py` 中新增 `_parse_playback_error()`）

理由：原始输出已有完整的 raw stdout/stderr，后端正则解析后通过 `error_info` 字段一并返回，前端直接消费结构化数据。前端也保留原始文本供高级用户排查。

替代方案：前端解析 → 需要前端处理复杂正则和字符串匹配，且每次回放都要重传大段文本。

### 决策 2：正则匹配策略
**选择：按错误类型分组匹配**

覆盖四种常见 Playwright 错误：
| 错误类型 | 正则模式 | 提取字段 |
|---------|---------|---------|
| `timeout` | `Locator\.(\w+):.*Timeout (\d+)ms exceeded` | 动作名、超时时间、向前搜索 selector |
| `strict_violation` | `strict mode violation: locator\((.+?)\) resolved to (\d+) elements` | selector、匹配数、元素列表 |
| `load_state_timeout` | `wait_for_load_state.*Timeout (\d+)ms exceeded` | state 类型、超时时间 |
| `assertion` | `expect\((.+?)\)\.to_(.+?)\(\)` 或 `AssertionError` | selector、期望状态 |

### 决策 3：前端展示方案
**选择：在 el-alert 下方新增结构化错误卡片**

- 有 `error_info` 时，在"失败" alert 下方显示结构化错误卡片
- 卡片包含：错误类型标签、定位器代码块、匹配元素（strict 时）、步骤提示
- 原始 stdout/stderr 改为 `el-collapse` 可折叠，默认收起

## 风险 / 权衡

| 风险 | 缓解措施 |
|------|---------|
| 新出现的 Playwright 错误格式无法匹配 | `error_info.type` 设为 `unknown`，仍然展示原始文本 |
| 中文提示覆盖不全 | 设计为可扩展的 if-else 结构，方便添加新类型 |
| 步骤序号提取不精确 | 基于堆栈中第几次 `_h_*` 调用来近似推断 |
