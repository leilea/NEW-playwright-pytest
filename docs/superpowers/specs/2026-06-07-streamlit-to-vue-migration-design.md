# Streamlit → Vue/TS + FastAPI 迁移设计稿

- 日期: 2026-06-07
- 状态: 已通过头脑风暴 (Q1-Q7 + Q2.5 + 6 项开放问题), 待用户审规格后进入实现计划
- 范围: 大型变更 (覆盖前后端 + 数据 + 权限 + 调度)
- 关联 OpenSpec 变更: 即将创建 `openspec/changes/2026-06-07-streamlit-to-vue-migration/`

## 1. 目标与动机

把当前 Streamlit 单体仪表盘 (1000 行 `page_testcases.py` + 4 个简化页) 替换为 **Vue 3 + TypeScript SPA + FastAPI 后端**, 同时补齐多用户、权限、定时任务三个缺口, 并为未来接 SSO 留出零侵入升级路径。

### 1.1 不做 (Day-1)

- AI 自愈 / 验证码识别 / RAG 知识库 (单独 future epic, 见 §13.2)
- DB 高级特性 (PostGIS / 读写分离 / 逻辑复制)
- 多节点部署 (K8s / Helm) — 单 docker-compose 起步
- 分布式任务队列 (Celery / Temporal)

### 1.2 保留

- Playwright + pytest + page_repository 完全不动
- `lib/web_actions` / `lib/api_actions` / `page_factory/page_repository` 业务逻辑不动
- 旧 JSON 数据 (suites / testcases) 一次性可选导入 PG, 导入完保留原位 (默认不导入)

## 2. 架构总览

```
                    ┌─────────────────────────────────────┐
                    │      浏览器 (Vue 3 + TS SPA)        │
                    │  Element Plus + VxeTable + ECharts  │
                    │  Pinia / Vue Router / TanStack Query│
                    └──────────┬──────────┬───────────────┘
                          HTTP │          │ WebSocket
                               │          │ (run/rec/playback)
                               ▼          ▼
                    ┌─────────────────────────────────────┐
                    │   FastAPI (异步, 同进程调度)         │
                    │  ┌─────────────────────────────┐    │
                    │  │ Routers → Services → Repos  │    │
                    │  │ Auth (JWT + 依赖注入)       │    │
                    │  │ RBAC (assert_can)           │    │
                    │  │ APScheduler (AsyncIO)       │    │
                    │  │ WS 推流 (run/rec/playback)  │    │
                    │  └─────────────────────────────┘    │
                    └──────────┬──────────┬───────────────┘
                               │          │
                          SQLA │          │ 子进程
                               ▼          ▼
                    ┌──────────────┐  ┌─────────────────┐
                    │ PostgreSQL 16│  │ pytest / 录制 /  │
                    │ (docker,本地) │  │ playwright codegen│
                    └──────────────┘  └─────────────────┘
```

**单进程原则**: FastAPI 进程内跑 `uvicorn` + `AsyncIOScheduler`, 不引入 Redis / RabbitMQ。规模上来再拆。

## 3. 端口与部署

- 开发期 docker-compose 起 2 个服务: `postgres` (5432) + `app` (暴露 8000 = FastAPI, 5173 = Vite dev)
- 生产期 docker-compose 只暴露 8000, FastAPI 在同一进程 serve 静态 `frontend/dist` 资源, Vite dev 服务不挂载
- 网络: 默认同 docker 网络, 跨机时改 env 即可

## 4. 身份与权限 (含 SSO 钩子)

### 4.1 核心抽象

```python
# backend/auth/providers/base.py
class LoginProvider(Protocol):
    async def authenticate(self, credential: Any) -> UserInfo: ...

# backend/auth/providers/local.py
class LocalPasswordProvider:
    """Day-1 实现: 邮箱 + 密码 (argon2id 哈希)"""

# backend/auth/providers/oidc.py  ← 未来实现
class OidcProvider:
    """Day-N 实现: OIDC 走 DSEP SSO"""
```

### 4.2 User 表关键字段

| 字段 | 类型 | 备注 |
|------|------|------|
| `id` | UUID | PK |
| `email` | citext, UNIQUE | **SSO 关联键** |
| `display_name` | text | |
| `password_hash` | text NULL | 本地登录用, SSO 用户 NULL |
| `provider` | text DEFAULT 'local' | `'local'` / `'oidc'` / 未来 `'ldap'` |
| `external_id` | text NULL | SSO subject |
| `is_active` | bool | |
| `created_at` | timestamptz | |

### 4.3 4 个零侵入升级钩子

1. `LoginProvider` 协议 + 实现注册表
2. User 表预留 `provider` / `external_id` / nullable `password_hash`
3. JWT payload 只含 `sub` (user_id) + `exp`, 不含密码 / 凭据
4. 首次 SSO 登录: 按 email 查本地 user → 不存在则 JIT 创建 (display_name, role=viewer 默认) → 后续按 `provider+external_id` 匹配

**补 SSO 工期**: ~2-3 天, 只新写 `OidcProvider` 实现, 不需全栈重构。

### 4.4 RBAC (角色 + 资源 ACL)

```sql
CREATE TYPE role_name AS ENUM ('admin', 'editor', 'viewer');
CREATE TABLE user_role (
    user_id UUID, role role_name, PRIMARY KEY (user_id, role)
);

CREATE TABLE resource_acl (
    id BIGSERIAL PK,
    resource_type TEXT,  -- 'suite' | 'case' | 'config'
    resource_id BIGINT,
    principal_type TEXT, -- 'user' | 'role'
    principal_id UUID,   -- user_id or role enum cast
    permission TEXT,     -- 'read' | 'write' | 'delete' | 'execute'
    UNIQUE (resource_type, resource_id, principal_type, principal_id, permission)
);
```

**检查入口**:
- 路由层: `Depends(check_permission("suite", suite_id, "read"))`
- service 层: `assert_can(user, "case", case_id, "write")`
- 业务层**永远不直接查表**, 统一走 `assert_can`

**升级路径**: 换 ABAC / Casbin 时, 只改 `assert_can` 实现, 业务代码 0 行改动。

## 5. 数据库与持久化

### 5.1 Schema (单库, 按域分 schema)

```
dsep_test
├── auth      (users, roles, resource_acl, login_audit)
├── catalog   (suites, cases, steps, recordings)
├── runtime   (runs, run_steps, playback_history, schedules)
└── audit     (login_audit, run_audit)
```

### 5.2 关键表 DDL (摘)

```sql
-- catalog
CREATE TABLE catalog.suite (
    id BIGSERIAL PK,
    name TEXT NOT NULL,
    description TEXT,
    env TEXT NOT NULL,          -- 'dsep' | 'demoqa'
    owner_id UUID NOT NULL,     -- -> auth.user
    created_at, updated_at
);

CREATE TABLE catalog.case (
    id BIGSERIAL PK,
    suite_id BIGINT -> catalog.suite,
    name TEXT NOT NULL,
    steps JSONB NOT NULL,       -- [{action, locator, value, ...}, ...]
    tags TEXT[],
    owner_id UUID,
    created_at, updated_at
);

-- runtime
CREATE TABLE runtime.run (
    id BIGSERIAL PK,
    suite_id BIGINT,
    env TEXT, browser TEXT,     -- 'chromium' | 'firefox' | 'webkit'
    status TEXT,                -- 'pending' | 'running' | 'passed' | 'failed' | 'cancelled'
    started_at, finished_at,
    triggered_by TEXT,          -- 'user' | 'schedule'
    schedule_id BIGINT NULL,
    log_path TEXT,
    exit_code INT
);

CREATE TABLE runtime.schedule (
    id BIGSERIAL PK,
    suite_id BIGINT,
    cron TEXT NOT NULL,         -- '0 2 * * *'
    enabled BOOL,
    next_run_at TIMESTAMPTZ,
    last_run_id BIGINT,
    created_by UUID
);
```

### 5.3 数据迁移 (JSON → PG, 默认不导入)

- **默认行为**: 不导入 (从零开始), 旧 JSON 文件保留原位
- **可选脚本**: `scripts/import_legacy_json.py`, 仅导入 suites + testcases; playback_history / trends 不导入
- 行级 try/except, 失败行落 `_import_errors.log`, 不阻塞整体
- 校验脚本: `scripts/verify_legacy_migration.py`, 手动可跑 (不进 CI)
- 文档: README "如需回滚" 段落引用此脚本

## 6. 部署

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: dsep_test
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
    volumes:
      - ./.data/pgdata:/var/lib/postgresql/data
    ports: ["5432:5432"]
  app:
    build: .
    depends_on: [postgres]
    env_file: .env
    ports: ["8000:8000"]   # FastAPI (生产还 serve frontend/dist)
                ["5173:5173"] # Vite dev (仅开发期)
```

`.env` 关键项:
```
DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/dsep_test
JWT_SECRET=<dev-only-32B>
JWT_TTL_HOURS=12
BOOTSTRAP_ADMIN_EMAIL=admin@local
BOOTSTRAP_ADMIN_PASSWORD=admin123
BOOTSTRAP_ADMIN_DISPLAY_NAME=系统管理员
```

## 7. 后端设计 (FastAPI)

### 7.1 目录结构

```
backend/
├── main.py                  # FastAPI 入口, lifespan 起调度器
├── deps.py                  # get_db, get_current_user
├── auth/
│   ├── jwt.py               # 签发/校验
│   ├── providers/
│   │   ├── base.py
│   │   └── local.py
│   └── rbac.py              # assert_can
├── routers/
│   ├── auth.py              # POST /login /refresh /logout /me
│   ├── suites.py
│   ├── cases.py
│   ├── runs.py              # POST 同步启动
│   ├── ws.py                # /ws/run /ws/rec /ws/playback
│   ├── schedules.py
│   ├── reports.py
│   ├── config.py
│   └── health.py            # /api/health/browsers
├── services/                # 业务编排 (reuses 现有 services/*)
│   ├── suite_service.py
│   ├── case_service.py
│   ├── run_service.py
│   ├── playback_service.py
│   └── scheduler_service.py
├── repos/                   # SQLAlchemy 2.x async
│   ├── models.py            # 全部 ORM 模型
│   ├── session.py
│   └── *.py
├── workers/                 # 子进程封装
│   ├── pytest_runner.py
│   ├── recorder.py          # playwright codegen
│   └── playback.py
├── scheduler/
│   └── jobs.py              # APScheduler job 定义
├── migrations/              # Alembic
└── tests/                   # pytest (后端)
```

### 7.2 关键路由

```
POST   /api/auth/login            {email, password} -> {token, user}
GET    /api/auth/me
GET    /api/suites?env=dsep
POST   /api/suites                {name, env} -> Suite
GET    /api/suites/{id}
PATCH  /api/suites/{id}
DELETE /api/suites/{id}
GET    /api/suites/{id}/cases
POST   /api/suites/{id}/cases
PATCH  /api/cases/{id}
POST   /api/cases/{id}/playback   -> 200 {playback_id}
GET    /api/runs?suite_id=&limit=
GET    /api/runs/{id}             -> 含 log tail
GET    /api/reports/{run_id}/allure
WS     /ws/run/{run_id}           server -> client: log lines
WS     /ws/rec                    client: actions -> server: {action, locator, value}
WS     /ws/playback/{case_id}     server -> client: step log + screenshot paths
GET    /api/schedules
POST   /api/schedules             {suite_id, cron, enabled}
PATCH  /api/schedules/{id}
POST   /api/schedules/{id}/trigger
WS     /ws/schedule/{id}          server -> client: job events
GET    /api/health/browsers       -> ['chromium','firefox','webkit']
```

### 7.3 录制 / 回放 / pytest 推流

- **录制**: 前端 WS 打开, 服务端起 `playwright codegen --target python -o tmp.py`, 把 codegen 输出动作通过 WS 推到前端, 实时渲染步骤表 (用户可在收尾后改 / 删 / 加)
- **回放**: 前端 `POST /cases/{id}/playback` → 后端起 `pytest` 子进程, 逐行读 stdout → WS 推送 `{step, status, log_line, screenshot?}`; 失败时自动截图 `artifacts/run_{id}/fail_{step}.png`
- **pytest run**: 同样的子进程 + WS 模式, 触发来源是用户 / 调度器

### 7.4 错误处理

- 统一异常 → `HTTPException(status, code, message, detail)`
- 全局 handler: `app.add_exception_handler(AppError, ...)`
- 业务层抛 `AppError("CASE_NOT_FOUND", 404)`, 不抛裸 Exception
- 422 校验错误: pydantic 自动, 不自定义

### 7.5 测试

- `pytest` + `httpx.AsyncClient` 测路由
- service 层单测
- repo 层用 `pytest-asyncio` + 测试 schema (单独 database)
- 目标: 80% 行覆盖, 关键路径 100% (auth, rbac, run_service, scheduler)

## 8. 前端设计 (Vue 3 + TS)

### 8.1 目录结构

```
frontend/
├── package.json             # pnpm
├── vite.config.ts
├── tsconfig.json            # strict
├── index.html
└── src/
    ├── main.ts
    ├── App.vue
    ├── router/
    │   ├── index.ts         # /login, /, /runs, /cases, /reports, /config, /admin
    │   └── guards.ts        # auth + permission
    ├── stores/              # Pinia
    │   ├── auth.ts
    │   ├── ui.ts
    │   └── filters.ts
    ├── api/                 # 封装 fetch + TanStack Query hooks
    │   ├── client.ts        # axios + JWT 注入 + 401 拦截
    │   ├── suites.ts
    │   ├── cases.ts
    │   ├── runs.ts
    │   └── ws.ts            # WebSocket 客户端封装
    ├── pages/
    │   ├── Login.vue
    │   ├── Dashboard.vue    # 5 指标 + ECharts 饼 / 柱 / 线
    │   ├── Runs.vue         # 实时流日志
    │   ├── Cases.vue        # VxeTable + 步骤编辑器
    │   ├── Reports.vue
    │   ├── Config.vue
    │   ├── Schedules.vue
    │   └── Admin.vue        # 用户 / 角色管理
    ├── components/
    │   ├── CaseTable.vue
    │   ├── StepEditor.vue   # VxeTable 列: action/locator/value/timeout/desc
    │   ├── RecorderPanel.vue
    │   ├── PlaybackStream.vue
    │   ├── RunLog.vue
    │   └── Charts/
    ├── types/               # 后端模型对应的 TS 类型
    ├── utils/
    └── tests/               # Vitest
```

### 8.2 关键设计

- **状态分层**: Pinia 存 UI / 筛选器, TanStack Query 存服务端数据 (缓存 / 重试 / 轮询 / 失效)
- **WS 客户端**: 抽 `useWs(url, onMessage)` 组合式, 自动重连 + 心跳
- **步骤编辑器**: VxeTable 可编辑列, action 枚举 (11 种) 用下拉; 录制回填时新增一行临时态, 用户可改 / 删
- **图表迁移**:
  - Plotly 饼 → ECharts `pie`
  - Plotly 柱 → ECharts `bar`
  - Plotly 折线 → ECharts `line` + dataZoom
- **表格迁移**:
  - 仪表盘最近结果表 → Element Plus `el-table` (行数少)
  - 用例列表 / 步骤编辑 → VxeTable (1000+ 行虚拟滚动)
  - 套件 / 用例 CRUD 表单 → Element Plus `el-form`
- **路由守卫**: meta.requires 数组, 登录态 + 资源权限检查
- **Feature Flag**: `VITE_FRONTEND_ENABLED=true|false`, false 时后端路由全返 404, 仍走 Streamlit

### 8.3 测试

- Vitest 测 stores / utils / api 封装
- `@vue/test-utils` 测关键组件 (CaseTable, StepEditor, PlaybackStream)
- Playwright 测 5 个核心 E2E: 登录 → 选套件 → 启动运行 → 看到实时日志 → 查报告

## 9. 定时任务

### 9.1 配置

```python
# backend/scheduler/jobs.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

scheduler = AsyncIOScheduler(
    jobstores={"default": SQLAlchemyJobStore(url=settings.database_url)},
    executors={"default": AsyncIOExecutor()},
)
```

### 9.2 Job 生命周期

- `POST /api/schedules {suite_id, cron}` → 写 DB → 启 APScheduler job
- job 触发 → 调 `run_service.start_scheduled(suite_id, schedule_id)` → 创建 `runtime.run` (triggered_by='schedule') → 起 pytest 子进程 → 推流到所有连 `/ws/schedule/{id}` 的前端
- job 失败 (pytest exit != 0): 不自动重跑, 记录 `last_error`, 由用户决定
- 应用重启: APScheduler 从 SQLAlchemyJobStore 读 job 列表, 续上

### 9.3 "定时任务" 页面

- 列表: 套件 / cron / 启停状态 / 下次运行 / 上次结果
- 操作: 启停切换 / 立即触发 / 编辑 cron / 删
- 实时: 选中 schedule 后开 WS, 看历史触发的事件流

### 9.4 升级路径

`SchedulerService` 协议化, 业务代码只调 `scheduler_service.create_job(...)`, 未来换 Celery Beat 不动业务。

## 10. 迁移分阶段 (5 阶段)

| 阶段 | 内容 | 入口默认 | 退出条件 |
|------|------|---------|---------|
| 1. 骨架 | docker-compose + FastAPI 空壳 + Vue 空壳 + 登录页 + Alembic 初始 | Streamlit | 登录可走, 新 DB 空表齐 |
| 2. 数据双写 | Streamlit 现有写操作 (改 / 增 / 删) 改为同时写 PG; FastAPI 后端读全走 PG; Streamlit 读仍走 JSON; 旧 JSON → PG 一次性导入作为可选前置 | Streamlit | 7 天一致性校验 0 差异 (Streamlit 写一条, PG 必有一条) |
| 3. 按页切 | 先切仪表盘 / 报告 / 系统配置 (静态读) → 测试运行 (含 WS) → 测试用例 (含步骤编辑 + 录制 + 回放) | Feature Flag | 5 页全功能 Vue 化, 用户切到 Vue 无感 |
| 4. 关 Streamlit 入口 | `VITE_FRONTEND_ENABLED` 默认 true; Streamlit 入口改 banner "已迁移, 请用新地址"; 旧 JSON 归档 | Vue | 30 天无 Streamlit 报错 |
| 5. 收尾 | 删 streamlit_app/ + 清理 .streamlit/ + 清理 conftest / pytest.ini / Dockerfile 里 streamlit 相关配置 | Vue | 仓库 `rg streamlit` 无业务引用, 仅历史 spec / 文档可保留 |

**回滚机制**: 任何阶段, 把 `VITE_FRONTEND_ENABLED=false` + Streamlit 入口恢复 banner 即可, 不需数据回滚 (PG 是 source of truth, 旧 JSON 是 archive)。

## 11. 风险与缓解

| 风险 | 影响 | 缓解 |
|------|------|------|
| sync → async 改造踩坑 | services / utils 异步化 ~3 天估时偏差 | 阶段 1 先做 PoC: 跑通一个 service 的 async 路径, 校准工期 |
| 录制流中断 | codegen 进程被网络 / 资源杀死 | WS 重连 + 客户端保存草稿到 localStorage, 重连后回填 |
| 调度器重启丢任务 | APScheduler 短暂重启期不触发 | SQLAlchemyJobStore 持久化 + `misfire_grace_time=300s` |
| VxeTable 学习曲线 | 步骤编辑器延期 | 阶段 3 单独留 PoC 周, 不达标就回退 Element Plus + 分页 |
| RBAC 权限漏洞 | 用户看到不该看的用例 | 路由层 + service 层双校验, 测试覆盖所有 403 路径 |
| 数据迁移丢行 | 旧 JSON 损坏行 | 行级 try/except, 错误行落 `_import_errors.log`, 不阻塞 |

## 12. 工期估算 (1 人, 全职)

| 阶段 | 估时 |
|------|------|
| 1. 骨架 | 5 天 |
| 2. 数据双写 | 4 天 |
| 3a. 静态页 (仪表盘 / 报告 / 配置) | 4 天 |
| 3b. 测试运行 (WS 推流) | 3 天 |
| 3c. 测试用例 (步骤编辑 + 录制 + 回放) | 8 天 |
| 3d. 定时任务页 | 2 天 |
| 4. 关 Streamlit 入口 | 1 天 |
| 5. 收尾 | 1 天 |
| **小计** | **28 天 (5.5 周)** |

不含: 文档、code review、bug 修复 (~+30%) → 实际 ~7-8 周。

## 13. 附加

### 13.1 种子管理员 (Bootstrap Admin)

- 启动时 (FastAPI lifespan hook) 检查: `auth.users` 表空 **AND** `BOOTSTRAP_ADMIN_EMAIL` + `BOOTSTRAP_ADMIN_PASSWORD` 都设了 → 建账号
- 安全约束:
  - 仅 users 表空时生效, 防覆盖
  - 密码用 argon2id 哈希
  - 自动赋 `admin` 角色
- 文档: README 显式提示 "生产部署请清掉 BOOTSTRAP_* 变量, 用 Admin 页建账号"
- Dev 默认值: `admin@local` / `admin123` / `系统管理员`

### 13.2 AI Future Epic 锚点

- 文件: `openspec/changes/_future/ai-integration.md` (空 stub)
- 触发条件: 用户明确要求启用 / 业务指标证明 ROI
- 范围 (待细化): provider / model 可配置 / 护栏 / 降级
- 工期: 单独 OpenSpec 变更, 估时 2-3 周
- 备注: Day-1 **不实现**, **不预留** schema / 字段, 保持代码干净

### 13.3 多浏览器矩阵

- 保留 chromium / firefox / webkit 三选一
- 路由: `GET /api/health/browsers` 返回本机已安装的浏览器列表
- 前端运行页"浏览器"下拉用此 API 数据, 不写死

## 14. 已确认的开放问题

| # | 问题 | 答复 |
|---|------|------|
| 1 | 端口 (FastAPI 8000 + Vite 5173) | 接受默认 |
| 2 | 种子管理员凭据 | `admin@local` / `admin123` 走 .env 种子 |
| 3 | 浏览器矩阵 | 保留 chromium / firefox / webkit 三选一 |
| 4 | 旧 JSON 回灌范围 | 仅回灌 suites + cases, playback_history 不回灌 |
| 5 | 种子数据 | 从零开始 (不带现网种子) |
| 6 | AI future stub | 同意留 `openspec/changes/_future/ai-integration.md` |
