# AGENTS.md — 项目级 AI 行为规约（全局强制）

> 本文件由项目根 `opencode.json` 的 `instructions` 字段自动加载，**每个会话都会自动注入**。
> 与 `CLAUDE.md` 并存：CLAUDE.md 记录 superpowers-zh 技能清单；本文件记录**强制行为规约**。

## 红线（不可绕过）

1. **Superpowers 全程在线**
   - 每个任务**第一步**必须调用 `using-superpowers` 技能（确认协议）
   - 然后根据下表调用对应的流程技能
   - 即使是"简单问题"也要走流程

2. **OpenSpec 变更流程**
   - 任何代码变更（功能 / Bug 修复 / 重构 / 配置 / 测试调整）**必须**走：
     `openspec-propose` → `openspec-apply-change` → `openspec-archive-change`
   - 唯一豁免：纯文档错别字、纯注释修改、CI 配置微小调整
   - 豁免时必须在提交信息中说明

3. **完成前验证**
   - 任何"完成"声明前必须运行验证命令并贴出输出
   - 不接受"应该可以工作"这类断言

## 任务路由表

| 任务信号 | 必调用顺序 |
|---------|----------|
| "实现 X 功能" / "添加 X" / "改 X 行为" | `brainstorming` → `openspec-propose` → `openspec-apply-change` → `verification-before-completion` → `openspec-archive-change` |
| "修复 bug" / "报错" / "测试失败" | `systematic-debugging` → `openspec-propose` → `openspec-apply-change` → `verification-before-completion` → `openspec-archive-change` |
| "重构" / "优化" / "改架构" | `openspec-propose` → `openspec-apply-change` → `verification-before-completion` |
| "改样式" / "调 UI" / "调 token" | `brainstorming` → `openspec-propose` → `openspec-apply-change` |
| 任务含 2+ 独立子任务 | 在 `brainstorming` 之后考虑 `dispatching-parallel-agents` |
| 收到 PR review / 代码审查反馈 | `receiving-code-review` |
| 准备合并 / 推送 | `requesting-code-review` → `finishing-a-development-branch` |
| 纯阅读 / 解释代码 / 提问题 | 仍需 `using-superpowers`，无需 OpenSpec |

## OpenSpec 速查

| 命令 | 何时用 |
|------|------|
| `/opsx:propose "想法"` | 任何变更前 |
| `/opsx:apply` | 按 tasks.md 实现 |
| `/opsx:explore` | 查看状态/规范 |
| `/opsx:archive <name>` | 验证通过后归档 |

## 优先级（冲突时）

1. **用户在当前消息中的明确指令**（最高）
2. **本文件（AGENTS.md）+ CLAUDE.md**
3. **Superpowers 技能内容**
4. **默认系统行为**（最低）

> 1% 可能性适用某个技能时，**必须**调用该技能。规则见 `using-superpowers` 技能 SKILL.md。

## 项目目录速查

- OpenSpec 规范：`openspec/specs/`
- OpenSpec 进行中变更：`openspec/changes/`
- OpenSpec 已归档变更：`openspec/changes/archive/`
- Superpowers 技能：`.claude/skills/<name>/SKILL.md`
- 项目级测试：`tests/`、`page_factory/`
- Vue 前端：`frontend/src/`

## 自动加载验证

启动 opencode 后，若本文件生效，会话开头应能引用以下内容：
- "AGENTS.md 已加载"
- "OpenSpec 强制流程已启用"
- "using-superpowers 已通过全局插件注入"

若未看到上述任一提示，检查 `.opencode/opencode.json` 是否被正确加载。
