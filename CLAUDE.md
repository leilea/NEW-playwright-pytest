<!-- superpowers-zh:begin (do not edit between these markers) -->
# Superpowers-ZH 中文增强版

本项目已安装 superpowers-zh 技能框架（20 个 skills）。

## 核心规则

1. **收到任务时，先检查是否有匹配的 skill** — 哪怕只有 1% 的可能性也要检查
2. **规范先于一切** — 每次开发新功能、修改问题或执行命令前，先使用 openspec propose 创建变更规范
3. **设计先于编码** — 收到功能需求时，先用 brainstorming skill 做需求分析
4. **测试先于实现** — 写代码前先写测试（TDD）
5. **验证先于完成** — 声称完成前必须运行验证命令

## 可用 Skills

Skills 位于 `.claude/skills/` 目录，每个 skill 有独立的 `SKILL.md` 文件。

- **brainstorming**: 在任何创造性工作之前必须使用此技能——创建功能、构建组件、添加功能或修改行为。在实现之前先探索用户意图、需求和设计。
- **chinese-code-review**: 中文 review 沟通参考——话术模板、分级标注（必须修复/建议修改/仅供参考）、国内团队常见反模式应对。仅在用户显式 /chinese-code-review 时调用，不要根据上下文自动触发。
- **chinese-commit-conventions**: 中文 commit 与 changelog 配置参考——Conventional Commits 中文适配、commitlint/husky/commitizen 中文模板、conventional-changelog 中文配置。仅在用户显式 /chinese-commit-conventions 时调用，不要根据上下文自动触发。
- **chinese-documentation**: 中文文档排版参考——中英文空格、全半角标点、术语保留、链接格式、中文文案排版指北约定。仅在用户显式 /chinese-documentation 时调用，不要根据上下文自动触发。
- **chinese-git-workflow**: 国内 Git 平台配置参考——Gitee、Coding.net、极狐 GitLab、CNB 的 SSH/HTTPS/凭据/CI 接入差异与镜像同步配置。仅在用户显式 /chinese-git-workflow 时调用，不要根据上下文自动触发。
- **dispatching-parallel-agents**: 当面对 2 个以上可以独立进行、无共享状态或顺序依赖的任务时使用
- **executing-plans**: 当你有一份书面实现计划需要在单独的会话中执行，并设有审查检查点时使用
- **finishing-a-development-branch**: 当实现完成、所有测试通过、需要决定如何集成工作时使用——通过提供合并、PR 或清理等结构化选项来引导开发工作的收尾
- **mcp-builder**: MCP 服务器构建方法论 — 系统化构建生产级 MCP 工具，让 AI 助手连接外部能力
- **receiving-code-review**: 收到代码审查反馈后、实施建议之前使用，尤其当反馈不明确或技术上有疑问时——需要技术严谨性和验证，而非敷衍附和或盲目执行
- **requesting-code-review**: 完成任务、实现重要功能或合并前使用，用于验证工作成果是否符合要求
- **subagent-driven-development**: 当在当前会话中执行包含独立任务的实现计划时使用
- **systematic-debugging**: 遇到任何 bug、测试失败或异常行为时使用，在提出修复方案之前执行
- **test-driven-development**: 在实现任何功能或修复 bug 时使用，在编写实现代码之前
- **using-git-worktrees**: 当需要开始与当前工作区隔离的功能开发，或在执行实现计划之前使用——通过原生工具或 git worktree 回退机制确保隔离工作区存在
- **using-superpowers**: 在开始任何对话时使用——确立如何查找和使用技能，要求在任何响应（包括澄清性问题）之前调用 Skill 工具
- **verification-before-completion**: 在宣称工作完成、已修复或测试通过之前使用，在提交或创建 PR 之前——必须运行验证命令并确认输出后才能声称成功；始终用证据支撑断言
- **workflow-runner**: 在 Claude Code / OpenClaw / Cursor 中直接运行 agency-orchestrator YAML 工作流——无需 API key，使用当前会话的 LLM 作为执行引擎。当用户提供 .yaml 工作流文件或要求多角色协作完成任务时触发。
- **writing-plans**: 当你有规格说明或需求用于多步骤任务时使用，在动手写代码之前
- **writing-skills**: 当创建新技能、编辑现有技能或在部署前验证技能是否有效时使用
- **openspec-propose**: 一步提案新变更并生成所有产出物（proposal.md、design.md、tasks.md）
- **openspec-apply-change**: 根据提案产出物实现变更
- **openspec-archive-change**: 归档已完成的变更并更新主规范
- **openspec-explore**: 探索和查看 OpenSpec 项目状态、变更和规范

## 如何使用

当任务匹配某个 skill 时，使用 `Skill` 工具加载对应 skill 并严格遵循其流程。绝不要用 Read 工具读取 SKILL.md 文件。

如果你认为哪怕只有 1% 的可能性某个 skill 适用于你正在做的事情，你必须调用该 skill 检查。

## OpenSpec 自动执行规则

每次执行命令、开发新功能、修改问题前，必须自动执行以下 OpenSpec 流程：

1. **提案先行** — 任何变更前先运行 `/opsx:propose` 或加载 `openspec-propose` skill 创建变更规范（proposal.md、design.md、tasks.md）
2. **按规范实现** — 提案通过后加载 `openspec-apply-change` skill 或运行 `/opsx:apply` 按 tasks.md 实现
3. **完成归档** — 实现验证通过后运行 `/opsx:archive` 或加载 `openspec-archive-change` skill 归档变更

### OpenSpec 命令

| 命令 | 说明 |
|------|------|
| `/opsx:propose "您的想法"` | 一步提案新变更，生成 proposal/design/tasks |
| `/opsx:apply` | 根据 tasks.md 实现变更 |
| `/opsx:explore` | 查看所有变更和规范状态 |
| `/opsx:archive <name>` | 归档已完成的变更 |

### 优先级

- **小修改（修复错字/简单配置）**：可直接修改，无需完整 openspec 流程
- **功能开发/Bug 修复/任何代码变更**：必须先走 openspec 提案→实现→归档流程
<!-- superpowers-zh:end -->

## 自动调用规则（强制性）

每次执行任务前，**必须按以下顺序自动调用三个技能框架**，不得跳过：

### 调用顺序

```
第 1 步 ── gstack（初始化 gstack 框架守卫）
第 2 步 ── using-superpowers（确认技能匹配与使用策略）
第 3 步 ── OpenSpec 流程（提案 → 实现 → 归档）
```

### 具体规则

| 阶段 | Skill | 触发条件 | 操作 |
|------|-------|---------|------|
| **初始化** | `gstack` | 每个任务开始时 | 调用 gstack 进行框架守卫初始化，确保后续所有操作在 gstack 管控下执行 |
| **技能路由** | `using-superpowers` | 每次对话首次任务 | 确立技能查找和使用策略，按流程图决定是否调用其他技能。同一对话后续任务可跳过 |
| **变更管理** | `openspec-propose` | 任何代码变更前 | 创建变更规范（proposal.md / design.md / tasks.md） |
| **实现执行** | `openspec-apply-change` | 提案通过后 | 按 tasks.md 实现变更 |
| **归档关闭** | `openspec-archive-change` | 实现验证通过后 | 归档已完成变更，更新主规范 |

### 例外

- **纯查询/信息获取**（不修改代码）：仅执行第 1、2 步，无需 OpenSpec
- **同一对话连续任务**：第 2 步（using-superpowers）仅在首次任务调用，后续任务从第 1 步开始
- **小修改（修复错字/简单配置）**：可直接修改，无需完整 OpenSpec 流程

### 红线

以下想法代表违规，必须停止：

| 违规想法 | 正确做法 |
|---------|---------|
| "这个任务太小了，不需要 gstack" | 任何任务都需要框架守卫 |
| "我已经知道 superpowers 怎么用了" | 正式调用确认，不依赖记忆 |
| "先做一点再走流程" | 流程必须在操作之前 |
| "让我先看看代码再决定" | 流程告诉你如何探索代码 |
