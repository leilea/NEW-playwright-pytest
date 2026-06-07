# AI Integration (Future Epic Stub)

> 占位文件, **Day-1 不实现, 不预留 schema**。作为 future epic 锚点存在, 单独 OpenSpec 变更实施时再激活。

## Why

未来可能加:
- 元素定位 AI 自愈 (locator 失效时自动重试 / 找替代)
- 验证码识别 (登录场景)
- RAG 知识库 (失败时拉历史 case + 文档辅助诊断)

## Why Not Now

- 用户明确决定 Day-1 关闭 AI 开关
- 不预留 `provider` / `model` / `confidence` 字段, 避免 schema 噪音
- 不引入 `mem0ai` / `langchain` / `openai` 依赖, requirements 保持干净

## Trigger Conditions (后续开启时)

满足任一:
- 用户 / 业务方明确要求启用
- 业务指标证明 ROI (例: 自愈率 > X%, 维护成本下降到 Y)
- 有专项预算 / 人力

## Scope (待细化, 开启时再 brainstorm)

- **可配置**: provider (OpenAI / Azure / 自建) / model / 温度 / 超时
- **护栏**: 置信度阈值, 失败回退, 不确定性高时回传统 Playwright
- **降级**: 离线 → 关闭 / 限流 → 排队 / 超时 → 报错
- **审计**: 调用次数 / 命中率 / 错误率, 走 `audit` schema

## 工期预估

单独 OpenSpec 变更, 估时 2-3 周 (1 人, 全职)。不计入本迁移 spec 工期。

## 关联

- 主迁移 spec: `docs/superpowers/specs/2026-06-07-streamlit-to-vue-migration-design.md` §13.2
- 当时安装但未用的依赖: `mem0ai` (在 `requirements.txt`)
