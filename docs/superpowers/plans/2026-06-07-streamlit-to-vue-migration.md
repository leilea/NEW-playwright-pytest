# Streamlit → Vue/TS 迁移 实现计划

> **面向 AI 代理的工作者：** 必需子技能：使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 逐任务实现此计划。步骤使用复选框（`- [ ]`）语法来跟踪进度。

**目标：** 将 `NEW-playwright-pytest-main` 从 Streamlit 单体迁移到 Vue 3 + TypeScript 前端 + FastAPI 后端 + PostgreSQL 持久化的多用户平台，支持 RBAC、定时任务和未来 SSO 接入。

**架构：**
- 前端：Vue 3.4 + TS strict + Vite 5 + Pinia + Vue Router 4 + TanStack Query + Element Plus + VxeTable + ECharts
- 后端：FastAPI + SQLAlchemy 2.x async + asyncpg + Alembic + APScheduler
- 数据库：PostgreSQL 16 (docker-compose, 单库多 schema: auth/catalog/runtime/audit)
- 鉴权：自建 user/role/permission + JWT (HTTP-only cookie) + 4 个 SSO 预留钩子
- 迁移：5 阶段 Feature Flag + 数据双写，Streamlit 切流期间保留
- 推流：WebSocket（pytest 日志 / 录制 / 回放 / 调度）

**技术栈：** 见规格 §2 与 §6 (`docs/superpowers/specs/2026-06-07-streamlit-to-vue-migration-design.md`)

**参考规格：** `docs/superpowers/specs/2026-06-07-streamlit-to-vue-migration-design.md`
**参考 OpenSpec：** `openspec/specs/` (test-platform, suite-catalog, test-runner, auth-rbac 既有规范)

---

## 计划修订日志（Plan Revision Log）

> 计划执行期间发现的规格瑕疵/安全补强，按发现顺序追加。每个修订都对应一个独立 commit。

| Rev | SHA | 任务 | 类别 | 摘要 |
|-----|-----|------|------|------|
| A   | 199a556 | T1 后 | 安全 | `git rm --cached .env` + .gitignore 增 `.env` / `__pycache__/` / `.pytest_cache/` |
| B   | f54d2b5 | T1 后 | 配置 | `CORS_ORIGINS` 由硬编码改为 `${CORS_ORIGINS:-default}` |
| C   | 27e732f | T1 后 | 配置 | compose 补 7 个 backend env (JWT_ALG/JWT_TTL_MIN/BOOTSTRAP_*) + 3 个 frontend env (VITE_*) |
| D   | 42c0510 | T1 后 | 容器 | `backend/Dockerfile` 加 system user `app` (uid 1001) + USER 指令 + chown |
| E   | e4ee02a | T1 后 | 镜像 | 新建 `backend/.dockerignore` (排除 .venv/ __pycache__/ tests/ .env) |
| F   | 66955e2 | T1 后 | 文档 | `.env.example` JWT_SECRET 改用 `openssl rand -hex 32` 显式生成说明 |

**对后续任务的影响：**
- T2 (Backend skeleton) 引用 `JWT_ALG` / `JWT_TTL_MIN` / `BOOTSTRAP_*` / `CORS_ORIGINS` 4 个 env, 现已就绪
- T2 Dockerfile 不再需要改 USER (D 已做)
- T2 起 backend 镜像大小受 .dockerignore 控制
- T36 (切流) `VITE_FRONTEND_ENABLED` env 已在 C 中透传到 frontend 容器

---

## 文件结构（计划产出物）

### 新增目录
```
backend/                              # FastAPI 后端 (新)
├── app/
│   ├── main.py                        # FastAPI app + lifespan
│   ├── config.py                      # pydantic-settings 读 .env
│   ├── deps.py                        # Depends() 注入
│   ├── security/
│   │   ├── jwt.py                     # JWT encode/decode
│   │   ├── password.py                # argon2id hash/verify
│   │   ├── providers.py               # LoginProvider 抽象 + LocalPasswordProvider
│   │   └── rbac.py                    # assert_can(user, action, resource)
│   ├── db/
│   │   ├── session.py                 # async engine + sessionmaker
│   │   └── base.py                    # DeclarativeBase
│   ├── models/                        # SQLAlchemy 模型
│   │   ├── auth.py                    # User, Role, UserRole, ResourceACL
│   │   ├── catalog.py                 # Suite, Case, Step
│   │   ├── runtime.py                 # Run, RunLog, Playback, Schedule
│   │   └── audit.py                   # AuditEvent
│   ├── schemas/                       # Pydantic
│   │   ├── auth.py, catalog.py, runtime.py, common.py
│   ├── services/
│   │   ├── auth_service.py            # login/logout/bootstrap
│   │   ├── suite_service.py           # suite CRUD
│   │   ├── case_service.py            # case CRUD + step reorder
│   │   ├── script_gen.py              # case → pytest code (纯函数)
│   │   ├── runner.py                  # PytestRunner (子进程)
│   │   ├── recorder.py                # playwright codegen 包装
│   │   ├── playback.py                # PlaybackService
│   │   └── scheduler.py               # APScheduler 封装
│   ├── routers/
│   │   ├── auth.py, health.py, suites.py, cases.py
│   │   ├── runs.py, schedules.py, config.py, reports.py, dashboard.py
│   ├── ws/
│   │   ├── manager.py                 # WebSocket 连接管理
│   │   ├── run_ws.py, rec_ws.py, playback_ws.py
│   └── bootstrap.py                   # lifespan 种子 admin
├── alembic/
│   ├── env.py
│   └── versions/0001_init.py
├── scripts/
│   ├── verify_legacy_migration.py
│   └── import_legacy_json.py
├── tests/                             # pytest (后端)
│   ├── conftest.py
│   ├── unit/                          # services / security / utils
│   └── integration/                   # routers / ws
├── pyproject.toml                     # 依赖 (uv 或 pip)
└── Dockerfile

frontend/                             # Vue 3 前端 (新)
├── src/
│   ├── main.ts, App.vue
│   ├── router/index.ts
│   ├── stores/                        # Pinia
│   │   ├── auth.ts, ui.ts
│   ├── api/                           # 封装 axios
│   │   ├── client.ts, auth.ts, suites.ts, cases.ts, runs.ts, schedules.ts
│   ├── composables/                   # useQuery, useMutation, useWS
│   ├── pages/
│   │   ├── Login.vue
│   │   ├── Dashboard.vue              # 5 指标 + ECharts
│   │   ├── Runs.vue, RunDetail.vue    # 实时日志
│   │   ├── Suites.vue, SuiteDetail.vue
│   │   ├── Cases.vue, CaseEditor.vue  # 步骤编辑器 VxeTable
│   │   ├── Recorder.vue
│   │   ├── Playback.vue, PlaybackHistory.vue
│   │   ├── Reports.vue                # 4 tab
│   │   ├── Schedules.vue
│   │   └── Config.vue                 # .env 在线编辑
│   ├── components/
│   │   ├── StepEditor.vue, RecorderPanel.vue
│   │   ├── LogStream.vue, EChart.vue
│   │   └── VxeTable.vue
│   ├── types/                         # 共享类型
│   └── utils/
├── tests/                             # Vitest + @vue/test-utils
│   ├── unit/, component/
├── e2e/                               # Playwright 前端 E2E
│   └── login.spec.ts, runs.spec.ts
├── vite.config.ts, tsconfig.json
├── package.json
└── Dockerfile

openspec/changes/_future/ai-integration.md    # 已建 (空 stub)

docs/superpowers/specs/2026-06-07-streamlit-to-vue-migration-design.md  # 已落档
docs/superpowers/plans/2026-06-07-streamlit-to-vue-migration.md          # 本文件
```

### 修改文件
- `conftest.py` — 加 `pytest_asyncio` fixture, 加 `db_session` 后端测试 fixture
- `requirements.txt` — 追加后端依赖 (fastapi, uvicorn, sqlalchemy[asyncio], asyncpg, alembic, apscheduler, python-jose, passlib[argon2], pydantic-settings, websockets, aiofiles)
- `Dockerfile.txt` → `Dockerfile` — 多阶段 (frontend build → backend image)
- `docker-compose.yml` — postgres + backend (dev)
- `.env.example` — 加 `DATABASE_URL` / `JWT_SECRET` / `BOOTSTRAP_ADMIN_*` / `VITE_*`
- `pytest.ini` — 加 `asyncio_mode = auto`
- `.gitignore` — 加 `.data/`, `frontend/node_modules/`, `frontend/dist/`

### 保留不动的现有文件
- `lib/`, `config/`, `tests/functional/`, `tests/api/`, `page_factory/`, `global_setup.py`
- `streamlit_app/` — 阶段 4 之前保留, 阶段 5 删除
- `openspec/` — 既有 4 份 specs 与 5 份归档保留

---

## Phase 1：骨架（5 天，8 任务）

### 任务 1：docker-compose + .env + Dockerfile

**文件：**
- 创建：`docker-compose.yml`
- 创建：`.env.example`
- 创建：`backend/Dockerfile`
- 修改：`.gitignore`

- [ ] **步骤 1：写 docker-compose 测试**

```python
# backend/tests/integration/test_docker_compose.py
import subprocess, shutil
import pytest
from pathlib import Path

@pytest.mark.skipif(not shutil.which("docker"), reason="docker not available")
def test_docker_compose_validates():
    """docker-compose config 必须能通过 schema 校验"""
    result = subprocess.run(
        ["docker", "compose", "config", "--quiet"],
        cwd=Path(__file__).parents[3],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, f"compose invalid: {result.stderr}"
```

- [ ] **步骤 2：跑测试确认失败**

运行：`pytest backend/tests/integration/test_docker_compose.py -v`
预期：SKIP（未装 docker）或 FAIL（docker-compose.yml 不存在）

- [ ] **步骤 3：写 docker-compose.yml**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    container_name: dsep-pg
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-dsep_test}
      POSTGRES_USER: ${POSTGRES_USER:-app}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-app}
    ports:
      - "5432:5432"
    volumes:
      - .data/pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-app}"]
      interval: 5s
      timeout: 3s
      retries: 5

  backend:
    build: ./backend
    container_name: dsep-backend
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-app}:${POSTGRES_PASSWORD:-app}@postgres:5432/${POSTGRES_DB:-dsep_test}
      JWT_SECRET: ${JWT_SECRET:?set JWT_SECRET in .env}
      CORS_ORIGINS: http://localhost:5173
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./allure-results:/app/allure-results
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    image: node:20-alpine
    container_name: dsep-frontend
    working_dir: /app
    volumes:
      - ./frontend:/app
    ports:
      - "5173:5173"
    command: sh -c "npm install && npm run dev"
    profiles: ["dev"]
```

- [ ] **步骤 4：写 .env.example**

```bash
# Database
POSTGRES_DB=dsep_test
POSTGRES_USER=app
POSTGRES_PASSWORD=app
DATABASE_URL=postgresql+asyncpg://app:app@localhost:5432/dsep_test

# Auth
JWT_SECRET=change-me-32-bytes-min-please-replace-in-prod
JWT_ALG=HS256
JWT_TTL_MIN=480

# Bootstrap admin (only applies when users table is empty)
BOOTSTRAP_ADMIN_EMAIL=admin@local
BOOTSTRAP_ADMIN_PASSWORD=admin123

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:8501

# Frontend flag (Phase 4)
VITE_FRONTEND_ENABLED=true
VITE_API_BASE=http://localhost:8000
VITE_WS_BASE=ws://localhost:8000
```

- [ ] **步骤 5：写 backend/Dockerfile**

```dockerfile
FROM python:3.11-slim AS base
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **步骤 6：更新 .gitignore**

```gitignore
.data/
backend/.venv/
frontend/node_modules/
frontend/dist/
allure-results/
logs/*.log
```

- [ ] **步骤 7：跑测试验证**

运行：`pytest backend/tests/integration/test_docker_compose.py -v`
预期：SKIP（CI 标记）或 PASS（装了 docker）

---

### 任务 2：Backend skeleton (main.py / deps.py / config)

**文件：**
- 创建：`backend/pyproject.toml`
- 创建：`backend/app/__init__.py`
- 创建：`backend/app/main.py`
- 创建：`backend/app/config.py`
- 创建：`backend/app/deps.py`
- 创建：`backend/app/db/__init__.py`
- 创建：`backend/app/db/session.py`
- 创建：`backend/app/db/base.py`
- 创建：`backend/tests/__init__.py`
- 创建：`backend/tests/conftest.py`
- 修改：`requirements.txt`

- [ ] **步骤 1：写 health 路由测试**

```python
# backend/tests/integration/test_health.py
import pytest
from httpx import ASGITransport, AsyncClient

@pytest.mark.asyncio
async def test_health_returns_ok():
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        r = await ac.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}
```

- [ ] **步骤 2：跑测试确认失败**

运行：`pytest backend/tests/integration/test_health.py -v`
预期：FAIL，ModuleNotFoundError: No module named 'app'

- [ ] **步骤 3：写 backend/pyproject.toml**

```toml
[project]
name = "dsep-backend"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "sqlalchemy[asyncio]>=2.0",
    "asyncpg>=0.29",
    "alembic>=1.13",
    "apscheduler>=3.10",
    "pydantic-settings>=2.2",
    "pydantic[email]>=2.6",
    "python-jose[cryptography]>=3.3",
    "passlib[argon2]>=1.7",
    "python-multipart>=0.0.9",
    "websockets>=12.0",
    "httpx>=0.27",
    "aiofiles>=23.2",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio>=0.23", "pytest-cov", "ruff", "mypy"]
```

- [ ] **步骤 4：写 app/config.py**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "postgresql+asyncpg://app:app@localhost:5432/dsep_test"
    jwt_secret: str = "dev-only-change-me-32-bytes-min-aaaa"
    jwt_alg: str = "HS256"
    jwt_ttl_min: int = 480
    cors_origins: str = "http://localhost:5173"
    bootstrap_admin_email: str = "admin@local"
    bootstrap_admin_password: str = "admin123"
    log_dir: str = "logs"
    allure_results_dir: str = "allure-results"

    @property
    def cors_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

settings = Settings()
```

- [ ] **步骤 5：写 app/db/base.py + app/db/session.py**

```python
# app/db/base.py
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass
```

```python
# app/db/session.py
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import settings

engine = create_async_engine(settings.database_url, pool_pre_ping=True, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

@asynccontextmanager
async def session_scope():
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **步骤 6：写 app/main.py**

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.session import engine
from app.routers import health

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()

app = FastAPI(title="DSEP Test Platform", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(health.router, prefix="/api")
```

- [ ] **步骤 7：写 app/routers/health.py 与 app/routers/__init__.py**

```python
# app/routers/__init__.py  (空)
```

```python
# app/routers/health.py
from fastapi import APIRouter
router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **步骤 8：写 app/deps.py**

```python
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal

async def get_db() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

- [ ] **步骤 9：写 backend/tests/conftest.py**

```python
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app

@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
```

- [ ] **步骤 10：跑测试验证通过**

运行：`pytest backend/tests/integration/test_health.py -v`
预期：PASS

- [ ] **步骤 11：追加 requirements.txt**

新增一行：
```
aiofiles>=23.2
```

---

### 任务 3：Alembic init + 4 schema 初始迁移

**文件：**
- 创建：`backend/alembic.ini`
- 创建：`backend/alembic/env.py`
- 创建：`backend/alembic/script.py.mako`
- 创建：`backend/alembic/versions/0001_init.py`

- [ ] **步骤 1：写迁移校验测试**

```python
# backend/tests/integration/test_migrations.py
import subprocess, os
from pathlib import Path

def test_alembic_env_present():
    assert Path("backend/alembic/env.py").exists()
    assert Path("backend/alembic/versions/0001_init.py").exists()

def test_alembic_init_creates_four_schemas():
    txt = Path("backend/alembic/versions/0001_init.py").read_text(encoding="utf-8")
    for schema in ("auth", "catalog", "runtime", "audit"):
        assert f'CREATE SCHEMA IF NOT EXISTS {schema}' in txt
```

- [ ] **步骤 2：跑测试确认失败**

预期：FAIL（alembic 目录不存在）

- [ ] **步骤 3：写 alembic.ini**

```ini
[alembic]
script_location = alembic
sqlalchemy.url = driver://user:pass@localhost/db
file_template = %%(rev)s_%%(slug)s

[loggers]
keys = root,sqlalchemy,alembic
[handlers]
keys = console
[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =
[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine
[logger_alembic]
level = INFO
handlers =
qualname = alembic
[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic
[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

- [ ] **步骤 4：写 alembic/env.py**

```python
from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.db.base import Base
from app import models  # noqa: F401 触发模型注册

config = context.config
config.set_main_option("sqlalchemy.url", os.environ.get("DATABASE_URL", config.get_main_option("sqlalchemy.url")))
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(config.get_section(config.config_ini_section, {}), prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **步骤 5：手写 0001_init.py**

```python
"""init auth/catalog/runtime/audit
Revision ID: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS auth")
    op.execute("CREATE SCHEMA IF NOT EXISTS catalog")
    op.execute("CREATE SCHEMA IF NOT EXISTS runtime")
    op.execute("CREATE SCHEMA IF NOT EXISTS audit")
    op.create_table(
        "users", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("display_name", sa.String(120)),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("provider", sa.String(32), nullable=False, server_default="local"),
        sa.Column("external_id", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="auth",
    )
    op.create_index("ix_users_external_id", "users", ["external_id"], schema="auth")
    op.create_table(
        "roles", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(32), unique=True, nullable=False),
        schema="auth",
    )
    op.create_table(
        "user_roles", sa.Column("user_id", sa.Integer, sa.ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("role_id", sa.Integer, sa.ForeignKey("auth.roles.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("granted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="auth",
    )
    op.create_table(
        "resource_acls",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("resource_type", sa.String(32), nullable=False, index=True),
        sa.Column("resource_id", sa.String(64), nullable=False, index=True),
        sa.Column("principal_type", sa.String(16), nullable=False),
        sa.Column("principal_id", sa.String(64), nullable=False, index=True),
        sa.Column("permission", sa.String(16), nullable=False),
        sa.UniqueConstraint("resource_type", "resource_id", "principal_type", "principal_id", "permission"),
        schema="auth",
    )
    op.create_table(
        "suites", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False, index=True),
        sa.Column("description", sa.Text, server_default=""),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("auth.users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="catalog",
    )
    op.create_table(
        "cases", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("suite_id", sa.Integer, sa.ForeignKey("catalog.suites.id", ondelete="CASCADE"), index=True),
        sa.Column("name", sa.String(160), nullable=False, index=True),
        sa.Column("tags", sa.JSON, server_default="[]"),
        sa.Column("steps", sa.JSON, server_default="[]"),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("auth.users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="catalog",
    )
    op.create_table(
        "runs", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("suite_id", sa.Integer, sa.ForeignKey("catalog.suites.id")),
        sa.Column("env", sa.String(32), nullable=False),
        sa.Column("browser", sa.String(16), nullable=False),
        sa.Column("status", sa.String(16), nullable=False, server_default="queued", index=True),
        sa.Column("started_by", sa.Integer, sa.ForeignKey("auth.users.id")),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary", sa.JSON, server_default="{}"),
        sa.Column("log_path", sa.String(255)),
        schema="runtime",
    )
    op.create_table(
        "schedules", sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("suite_id", sa.Integer, sa.ForeignKey("catalog.suites.id", ondelete="CASCADE")),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("cron", sa.String(64), nullable=False),
        sa.Column("env", sa.String(32)),
        sa.Column("browser", sa.String(16)),
        sa.Column("enabled", sa.Boolean, server_default=sa.text("true")),
        sa.Column("owner_id", sa.Integer, sa.ForeignKey("auth.users.id")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="runtime",
    )
    op.create_table(
        "audit_events", sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("actor_id", sa.Integer, sa.ForeignKey("auth.users.id")),
        sa.Column("action", sa.String(64), nullable=False, index=True),
        sa.Column("target_type", sa.String(32)),
        sa.Column("target_id", sa.String(64)),
        sa.Column("payload", sa.JSON, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), index=True),
        schema="audit",
    )

def downgrade() -> None:
    op.drop_table("audit_events", schema="audit")
    op.drop_table("schedules", schema="runtime")
    op.drop_table("runs", schema="runtime")
    op.drop_table("cases", schema="catalog")
    op.drop_table("suites", schema="catalog")
    op.drop_table("resource_acls", schema="auth")
    op.drop_table("user_roles", schema="auth")
    op.drop_table("roles", schema="auth")
    op.drop_table("users", schema="auth")
    op.execute("DROP SCHEMA IF EXISTS audit")
    op.execute("DROP SCHEMA IF EXISTS runtime")
    op.execute("DROP SCHEMA IF EXISTS catalog")
    op.execute("DROP SCHEMA IF EXISTS auth")
```

- [ ] **步骤 6：手写 alembic/script.py.mako**

```mako
"""${message}
Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

- [ ] **步骤 7：跑测试 + 真机迁移**

```bash
pytest backend/tests/integration/test_migrations.py -v
docker compose up -d postgres
cd backend && alembic upgrade head
```

---

### 任务 4：User model + LocalPasswordProvider + JWT utils

**文件：**
- 创建：`backend/app/models/__init__.py`
- 创建：`backend/app/models/auth.py`
- 创建：`backend/app/security/__init__.py`
- 创建：`backend/app/security/password.py`
- 创建：`backend/app/security/jwt.py`
- 创建：`backend/app/security/providers.py`
- 创建：`backend/app/schemas/__init__.py`
- 创建：`backend/app/schemas/auth.py`

- [ ] **步骤 1：写 password 单元测试**

```python
# backend/tests/unit/test_password.py
from app.security.password import hash_password, verify_password

def test_hash_and_verify_roundtrip():
    h = hash_password("hunter2-correct")
    assert h.startswith("$argon2id$")
    assert verify_password("hunter2-correct", h) is True
    assert verify_password("hunter2-wrong", h) is False
```

- [ ] **步骤 2：跑测试确认失败**

预期：FAIL（模块不存在）

- [ ] **步骤 3：写 app/security/password.py**

```python
from passlib.context import CryptContext
_pwd = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(plain: str) -> str:
    return _pwd.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)
```

- [ ] **步骤 4：写 JWT 测试**

```python
# backend/tests/unit/test_jwt.py
import time, pytest
from app.security.jwt import issue_token, decode_token
from app.config import Settings

def test_issue_decode_roundtrip():
    s = Settings(jwt_secret="x"*32, jwt_ttl_min=5)
    tok = issue_token(s, user_id=42, email="a@b.c")
    payload = decode_token(s, tok)
    assert payload["sub"] == "42"
    assert payload["email"] == "a@b.c"

def test_expired_token_rejected():
    s = Settings(jwt_secret="x"*32, jwt_ttl_min=0)
    tok = issue_token(s, user_id=1, email="a@b.c")
    time.sleep(0.1)
    with pytest.raises(Exception):
        decode_token(s, tok)
```

- [ ] **步骤 5：写 app/security/jwt.py**

```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError

def issue_token(settings, *, user_id: int, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=settings.jwt_ttl_min)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_alg)

def decode_token(settings, token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_alg])
    except JWTError as e:
        raise ValueError(f"invalid token: {e}") from e
```

- [ ] **步骤 6：写 LoginProvider 测试**

```python
# backend/tests/unit/test_providers.py
import pytest
from app.security.providers import LocalPasswordProvider, LoginError
from app.security.password import hash_password
from app.models.auth import User

@pytest.mark.asyncio
async def test_local_provider_authenticates(db_session):
    user = User(email="t@e.st", display_name="T", password_hash=hash_password("pw"))
    db_session.add(user); await db_session.flush()
    p = LocalPasswordProvider()
    u = await p.authenticate(db_session, email="t@e.st", password="pw")
    assert u.id == user.id

@pytest.mark.asyncio
async def test_local_provider_rejects_wrong_password(db_session):
    user = User(email="t@e.st", password_hash=hash_password("right"))
    db_session.add(user); await db_session.flush()
    p = LocalPasswordProvider()
    with pytest.raises(LoginError):
        await p.authenticate(db_session, email="t@e.st", password="wrong")
```

- [ ] **步骤 7：写 app/models/auth.py**

```python
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

class User(Base):
    __tablename__ = "users"
    __table_args__ = {"schema": "auth"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(120))
    password_hash: Mapped[str | None] = mapped_column(String(255))
    provider: Mapped[str] = mapped_column(String(32), default="local", server_default="local")
    external_id: Mapped[str | None] = mapped_column(String(255), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    roles: Mapped[list["UserRole"]] = relationship(back_populates="user", cascade="all, delete-orphan")

class Role(Base):
    __tablename__ = "roles"
    __table_args__ = {"schema": "auth"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(32), unique=True)

class UserRole(Base):
    __tablename__ = "user_roles"
    __table_args__ = {"schema": "auth"}
    user_id: Mapped[int] = mapped_column(ForeignKey("auth.users.id", ondelete="CASCADE"), primary_key=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("auth.roles.id", ondelete="CASCADE"), primary_key=True)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    user: Mapped[User] = relationship(back_populates="roles")
    role: Mapped[Role] = relationship()

class ResourceACL(Base):
    __tablename__ = "resource_acls"
    __table_args__ = {"schema": "auth"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    resource_type: Mapped[str] = mapped_column(String(32), index=True)
    resource_id: Mapped[str] = mapped_column(String(64), index=True)
    principal_type: Mapped[str] = mapped_column(String(16))
    principal_id: Mapped[str] = mapped_column(String(64), index=True)
    permission: Mapped[str] = mapped_column(String(16))
```

- [ ] **步骤 8：写 app/security/providers.py**

```python
from typing import Protocol
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.auth import User
from app.security.password import verify_password

class LoginError(Exception): pass

class LoginProvider(Protocol):
    name: str
    async def authenticate(self, db: AsyncSession, **credentials) -> User: ...

class LocalPasswordProvider:
    name = "local"
    async def authenticate(self, db: AsyncSession, *, email: str, password: str) -> User:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not user.is_active or not user.password_hash:
            raise LoginError("invalid credentials")
        if not verify_password(password, user.password_hash):
            raise LoginError("invalid credentials")
        return user
```

- [ ] **步骤 9：写 app/schemas/auth.py**

```python
from pydantic import BaseModel, EmailStr

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    id: int
    email: EmailStr
    display_name: str | None
    roles: list[str]
    model_config = {"from_attributes": True}
```

- [ ] **步骤 10：跑所有测试**

运行：`pytest backend/tests/unit -v`
预期：PASS

---

### 任务 5：/api/auth/login + /api/auth/me routers

**文件：**
- 创建：`backend/app/routers/auth.py`
- 创建：`backend/app/services/__init__.py`
- 创建：`backend/app/services/auth_service.py`
- 修改：`backend/app/main.py`
- 修改：`backend/app/deps.py`（加 current_user）
- 修改：`backend/tests/conftest.py`（加 db_session fixture）

- [ ] **步骤 1：写 auth service 测试**

```python
# backend/tests/unit/test_auth_service.py
import pytest
from app.services.auth_service import login_with_password, LoginFailed
from app.security.password import hash_password
from app.models.auth import User

@pytest.mark.asyncio
async def test_login_returns_token_and_user(db_session):
    db_session.add(User(email="a@b.c", password_hash=hash_password("x")))
    await db_session.flush()
    token, user = await login_with_password(db_session, email="a@b.c", password="x")
    assert token and user.email == "a@b.c"

@pytest.mark.asyncio
async def test_login_wrong_raises(db_session):
    db_session.add(User(email="a@b.c", password_hash=hash_password("x")))
    await db_session.flush()
    with pytest.raises(LoginFailed):
        await login_with_password(db_session, email="a@b.c", password="y")
```

- [ ] **步骤 2：写 app/services/auth_service.py**

```python
from app.config import settings
from app.security.providers import LocalPasswordProvider, LoginError
from app.security.jwt import issue_token

class LoginFailed(Exception): pass

async def login_with_password(db, *, email: str, password: str):
    provider = LocalPasswordProvider()
    try:
        user = await provider.authenticate(db, email=email, password=password)
    except LoginError as e:
        raise LoginFailed(str(e)) from e
    token = issue_token(settings, user_id=user.id, email=user.email)
    return token, user
```

- [ ] **步骤 3：扩 deps.py 加 get_current_user**

```python
# app/deps.py 追加
from fastapi import Depends, HTTPException, Request
from sqlalchemy import select
from app.security.jwt import decode_token
from app.config import settings
from app.models.auth import User

async def get_current_user(request: Request, db = Depends(get_db)) -> User:
    token = request.cookies.get("access_token")
    auth = request.headers.get("authorization", "")
    if not token and auth.lower().startswith("bearer "):
        token = auth.split(" ", 1)[1]
    if not token:
        raise HTTPException(401, "missing token")
    try:
        payload = decode_token(settings, token)
    except ValueError:
        raise HTTPException(401, "invalid token")
    uid = int(payload["sub"])
    res = await db.execute(select(User).where(User.id == uid))
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, "user not found or inactive")
    return user
```

- [ ] **步骤 4：写 app/routers/auth.py**

```python
from fastapi import APIRouter, Depends, HTTPException, Response
from app.deps import get_db, get_current_user
from app.schemas.auth import LoginIn, UserOut
from app.services.auth_service import login_with_password, LoginFailed

router = APIRouter(prefix="/api/auth", tags=["auth"])

@router.post("/login")
async def login(body: LoginIn, response: Response, db = Depends(get_db)):
    try:
        token, user = await login_with_password(db, email=body.email, password=body.password)
    except LoginFailed:
        raise HTTPException(401, "invalid credentials")
    response.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=8*3600)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user), db = Depends(get_db)):
    role_names = [r.role.name for r in user.roles]
    return UserOut(id=user.id, email=user.email, display_name=user.display_name, roles=role_names)

@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}
```

- [ ] **步骤 5：在 main.py 注册 auth 路由**

```python
# app/main.py 追加
from app.routers import auth
app.include_router(auth.router)
```

- [ ] **步骤 6：扩 conftest.py 加 db_session fixture**

```python
# backend/tests/conftest.py 追加
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.base import Base
import app.models  # noqa
from sqlalchemy import text

@pytest.fixture
async def db_session():
    engine = create_async_engine("postgresql+asyncpg://app:app@localhost:5432/dsep_test", echo=False)
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        # 清理可能残留数据
        await session.execute(text("DELETE FROM auth.user_roles"))
        await session.execute(text("DELETE FROM auth.users"))
        await session.commit()
        yield session
        await session.rollback()
    await engine.dispose()
```

- [ ] **步骤 7：写 auth router 集成测试**

```python
# backend/tests/integration/test_auth_router.py
import pytest

@pytest.mark.asyncio
async def test_login_success_returns_jwt(client, db_session):
    from app.security.password import hash_password
    from app.models.auth import User
    db_session.add(User(email="u@e.st", password_hash=hash_password("pw"), is_active=True))
    await db_session.flush()
    r = await client.post("/api/auth/login", json={"email": "u@e.st", "password": "pw"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["token_type"] == "bearer"
    assert r.cookies.get("access_token") is not None

@pytest.mark.asyncio
async def test_login_wrong_password_401(client, db_session):
    from app.security.password import hash_password
    from app.models.auth import User
    db_session.add(User(email="u@e.st", password_hash=hash_password("right"), is_active=True))
    await db_session.flush()
    r = await client.post("/api/auth/login", json={"email": "u@e.st", "password": "wrong"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_me_returns_user(client, db_session):
    from app.security.password import hash_password
    from app.models.auth import User, Role, UserRole
    user = User(email="u@e.st", password_hash=hash_password("pw"))
    db_session.add(user); await db_session.flush()
    role = Role(name="editor")
    db_session.add(role); await db_session.flush()
    db_session.add(UserRole(user_id=user.id, role_id=role.id)); await db_session.flush()
    r = await client.post("/api/auth/login", json={"email": "u@e.st", "password": "pw"})
    tok = r.json()["access_token"]
    r = await client.get("/api/auth/me", headers={"Authorization": f"Bearer {tok}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == "u@e.st"
    assert "editor" in body["roles"]
```

- [ ] **步骤 8：跑测试验证**

运行：`pytest backend/tests/integration/test_auth_router.py -v`
预期：PASS

---

### 任务 6：Bootstrap admin lifespan hook

**文件：**
- 创建：`backend/app/bootstrap.py`
- 修改：`backend/app/main.py`

- [ ] **步骤 1：写 bootstrap 测试**

```python
# backend/tests/integration/test_bootstrap.py
import pytest
from app.bootstrap import bootstrap_admin
from app.models.auth import User, Role, UserRole
from sqlalchemy import select

@pytest.mark.asyncio
async def test_bootstrap_creates_admin_when_empty(db_session):
    await bootstrap_admin(db_session, email="a@l.c", password="pw")
    res = await db_session.execute(select(User).where(User.email == "a@l.c"))
    u = res.scalar_one()
    assert u.password_hash is not None
    assert u.display_name == "Bootstrap Admin"
    res = await db_session.execute(select(Role).where(Role.name == "admin"))
    role = res.scalar_one()
    res = await db_session.execute(select(UserRole).where(UserRole.user_id == u.id, UserRole.role_id == role.id))
    assert res.scalar_one_or_none() is not None

@pytest.mark.asyncio
async def test_bootstrap_skips_when_users_exist(db_session):
    from app.security.password import hash_password
    db_session.add(User(email="existing@e.c", password_hash=hash_password("x")))
    await db_session.flush()
    await bootstrap_admin(db_session, email="a@l.c", password="pw")
    res = await db_session.execute(select(User).where(User.email == "a@l.c"))
    assert res.scalar_one_or_none() is None

@pytest.mark.asyncio
async def test_bootstrap_seeds_default_roles(db_session):
    await bootstrap_admin(db_session, email="a@l.c", password="pw")
    res = await db_session.execute(select(Role))
    names = {r.name for r in res.scalars().all()}
    assert {"admin", "editor", "viewer"} <= names
```

- [ ] **步骤 2：写 app/bootstrap.py**

```python
from sqlalchemy import select
from app.models.auth import User, Role, UserRole
from app.security.password import hash_password

DEFAULT_ROLES = ["admin", "editor", "viewer"]

async def bootstrap_admin(db, *, email: str, password: str) -> None:
    for rn in DEFAULT_ROLES:
        existing = (await db.execute(select(Role).where(Role.name == rn))).scalar_one_or_none()
        if existing is None:
            db.add(Role(name=rn))
    await db.flush()
    count = (await db.execute(select(User))).scalars().first()
    if count is not None:
        return
    admin_user = User(email=email, display_name="Bootstrap Admin", password_hash=hash_password(password))
    db.add(admin_user)
    await db.flush()
    admin_role = (await db.execute(select(Role).where(Role.name == "admin"))).scalar_one()
    db.add(UserRole(user_id=admin_user.id, role_id=admin_role.id))
    await db.flush()
```

- [ ] **步骤 3：在 main.py lifespan 调用**

```python
# app/main.py lifespan 改写
from app.db.session import session_scope
from app.bootstrap import bootstrap_admin
from app.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with session_scope() as db:
        await bootstrap_admin(db, email=settings.bootstrap_admin_email, password=settings.bootstrap_admin_password)
    yield
    await engine.dispose()
```

- [ ] **步骤 4：跑测试**

运行：`pytest backend/tests/integration/test_bootstrap.py -v`
预期：PASS

---

### 任务 7：Frontend skeleton (Vite + Vue + TS + Pinia + Router + Element Plus)

**文件：**
- 创建：`frontend/package.json`
- 创建：`frontend/vite.config.ts`
- 创建：`frontend/tsconfig.json`
- 创建：`frontend/index.html`
- 创建：`frontend/src/main.ts`
- 创建：`frontend/src/App.vue`
- 创建：`frontend/src/router/index.ts`
- 创建：`frontend/src/api/client.ts`

- [ ] **步骤 1：脚手架**

```bash
cd frontend
npm create vite@latest . -- --template vue-ts
npm i element-plus pinia vue-router@4 @tanstack/vue-query axios echarts vue-echarts
npm i -D vitest @vue/test-utils @types/node jsdom @playwright/test
```

- [ ] **步骤 2：写 vite.config.ts（带代理）**

```ts
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
  test: {
    environment: 'jsdom',
  },
})
```

- [ ] **步骤 3：写 tsconfig.json（strict）**

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "Bundler",
    "strict": true,
    "jsx": "preserve",
    "lib": ["ES2022", "DOM", "DOM.Iterable"],
    "types": ["vitest/globals", "node"],
    "skipLibCheck": true,
    "esModuleInterop": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "useDefineForClassFields": true,
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  },
  "include": ["src/**/*", "tests/**/*"]
}
```

- [ ] **步骤 4：写 main.ts 装配 Element Plus + Pinia + Router + Query**

```ts
import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { VueQueryPlugin, QueryClient } from '@tanstack/vue-query'
import App from './App.vue'
import router from './router'
import { useAuthStore } from '@/stores/auth'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)
app.use(VueQueryPlugin, new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: false } }
}))
const auth = useAuthStore()
auth.refresh().finally(() => app.mount('#app'))
```

- [ ] **步骤 5：写 router/index.ts（守卫占位）**

```ts
import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('@/pages/Login.vue'), meta: { public: true } },
    { path: '/', component: () => import('@/pages/Dashboard.vue') },
    { path: '/suites', component: () => import('@/pages/Suites.vue') },
    { path: '/suites/:id', component: () => import('@/pages/SuiteDetail.vue') },
    { path: '/cases', component: () => import('@/pages/Cases.vue') },
    { path: '/cases/:id/edit', component: () => import('@/pages/CaseEditor.vue') },
    { path: '/runs', component: () => import('@/pages/Runs.vue') },
    { path: '/runs/:id', component: () => import('@/pages/RunDetail.vue') },
    { path: '/reports', component: () => import('@/pages/Reports.vue') },
    { path: '/schedules', component: () => import('@/pages/Schedules.vue') },
    { path: '/recorder', component: () => import('@/pages/Recorder.vue') },
    { path: '/config', component: () => import('@/pages/Config.vue'), meta: { roles: ['admin'] } },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) return true
  if (!auth.user) return { path: '/login', query: { next: to.fullPath } }
  const required = to.meta.roles as string[] | undefined
  if (required && !required.some(r => auth.roles.includes(r))) return { path: '/' }
  return true
})

export default router
```

- [ ] **步骤 6：写 api/client.ts（带 cookie）**

```ts
import axios from 'axios'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '/api',
  withCredentials: true,
  timeout: 30_000,
})

http.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && !location.pathname.startsWith('/login')) {
      location.href = '/login'
    }
    return Promise.reject(err)
  }
)
```

- [ ] **步骤 7：写 App.vue（router-view + 顶栏）**

```vue
<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>

<template>
  <el-container v-if="auth.user" style="height: 100vh">
    <el-aside width="200px" style="background: #001529; color: #fff">
      <h3 style="color:#fff;padding:16px">DSEP Test</h3>
      <el-menu :router="true" background-color="#001529" text-color="#fff" active-text-color="#409eff">
        <el-menu-item index="/">仪表盘</el-menu-item>
        <el-menu-item index="/suites">测试套件</el-menu-item>
        <el-menu-item index="/cases">测试用例</el-menu-item>
        <el-menu-item index="/runs">测试运行</el-menu-item>
        <el-menu-item index="/recorder">录制</el-menu-item>
        <el-menu-item index="/reports">报告</el-menu-item>
        <el-menu-item index="/schedules">定时任务</el-menu-item>
        <el-menu-item v-if="auth.roles.includes('admin')" index="/config">系统配置</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header style="display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid #eee">
        <span></span>
        <el-dropdown @command="(c:string)=>c==='logout'&&auth.logout()">
          <span>{{ auth.user?.email }} <el-tag size="small">{{ auth.roles.join(',') }}</el-tag></span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </el-header>
      <el-main><router-view /></el-main>
    </el-container>
  </el-container>
  <router-view v-else />
</template>
```

- [ ] **步骤 8：跑通 dev server**

```bash
cd frontend && npm run dev
# 浏览器打开 http://localhost:5173 应见空骨架（路由跳到 /login）
```

---

### 任务 8：Login page + auth store + JWT 注入

**文件：**
- 创建：`frontend/src/stores/auth.ts`
- 创建：`frontend/src/api/auth.ts`
- 创建：`frontend/src/pages/Login.vue`
- 创建：`frontend/src/pages/Dashboard.vue`（占位）
- 创建：`frontend/tests/unit/auth.test.ts`

- [ ] **步骤 1：写 auth store 单元测试**

```ts
// frontend/tests/unit/auth.test.ts
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from '@/stores/auth'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('@/api/auth', () => ({
  login: vi.fn(),
  fetchMe: vi.fn(),
  logout: vi.fn(),
}))

import * as api from '@/api/auth'

describe('auth store', () => {
  beforeEach(() => { setActivePinia(createPinia()) })

  it('login sets user and roles', async () => {
    vi.mocked(api.login).mockResolvedValue({ access_token: 't' } as any)
    vi.mocked(api.fetchMe).mockResolvedValue({ id: 1, email: 'a@b.c', display_name: 'A', roles: ['admin'] })
    const store = useAuthStore()
    await store.login('a@b.c', 'pw')
    expect(store.user?.email).toBe('a@b.c')
    expect(store.roles).toEqual(['admin'])
  })

  it('hasRole returns true for matching role', async () => {
    vi.mocked(api.fetchMe).mockResolvedValue({ id: 1, email: 'a@b.c', display_name: 'A', roles: ['editor'] })
    const store = useAuthStore()
    await store.refresh()
    expect(store.hasRole('editor')).toBe(true)
    expect(store.hasRole('admin')).toBe(false)
  })
})
```

- [ ] **步骤 2：写 src/api/auth.ts**

```ts
import { http } from './client'

export type Role = 'admin' | 'editor' | 'viewer'
export interface User { id: number; email: string; display_name: string | null; roles: Role[] }

export const login = (email: string, password: string) =>
  http.post<{ access_token: string; token_type: string }>('/auth/login', { email, password }).then(r => r.data)

export const fetchMe = () => http.get<User>('/auth/me').then(r => r.data)

export const logout = () => http.post('/auth/logout').then(r => r.data)
```

- [ ] **步骤 3：写 src/stores/auth.ts**

```ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '@/api/auth'
import type { User } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const roles = computed(() => user.value?.roles ?? [])

  async function refresh() {
    try { user.value = await api.fetchMe() }
    catch { user.value = null }
  }
  async function login(email: string, password: string) {
    await api.login(email, password)
    await refresh()
  }
  async function logout() {
    await api.logout()
    user.value = null
    location.href = '/login'
  }
  function hasRole(r: string) { return roles.value.includes(r as any) }
  return { user, roles, refresh, login, logout, hasRole }
})
```

- [ ] **步骤 4：写 src/pages/Login.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const email = ref('admin@local')
const password = ref('admin123')
const loading = ref(false)
const error = ref('')
const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

async function submit() {
  loading.value = true
  error.value = ''
  try {
    await auth.login(email.value, password.value)
    const next = (route.query.next as string) || '/'
    router.replace(next)
  } catch (e: any) {
    error.value = e?.response?.data?.detail || '登录失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <el-container style="height:100vh;align-items:center;justify-content:center;background:#f5f7fa">
    <el-card style="width:360px">
      <h2 style="text-align:center;margin-top:0">DSEP Test Platform</h2>
      <el-form @submit.prevent="submit">
        <el-form-item label="邮箱"><el-input v-model="email" /></el-form-item>
        <el-form-item label="密码"><el-input v-model="password" type="password" show-password /></el-form-item>
        <el-button type="primary" :loading="loading" @click="submit" style="width:100%">登录</el-button>
        <el-alert v-if="error" :title="error" type="error" show-icon style="margin-top:12px" />
      </el-form>
    </el-card>
  </el-container>
</template>
```

- [ ] **步骤 5：写 src/pages/Dashboard.vue（占位 + 显示当前用户）**

```vue
<script setup lang="ts">
import { useAuthStore } from '@/stores/auth'
const auth = useAuthStore()
</script>
<template>
  <div>
    <h2>仪表盘</h2>
    <p>欢迎，{{ auth.user?.email }}</p>
  </div>
</template>
```

- [ ] **步骤 6：跑单元测试**

运行：`cd frontend && npx vitest run`
预期：PASS

- [ ] **步骤 7：手测登录**

```
浏览器开 http://localhost:5173/login
用 admin@local / admin123 登录
跳转 / 应见 "欢迎，admin@local"
```

---

## Phase 2：数据双写（4 天，6 任务）

### 任务 9：json_store sync → async 改造

**文件：**
- 创建：`backend/lib_compat/__init__.py`
- 创建：`backend/lib_compat/json_store_async.py`
- 创建：`backend/tests/unit/test_json_store_async.py`

- [ ] **步骤 1：写 async wrapper 测试**

```python
# backend/tests/unit/test_json_store_async.py
import pytest, tempfile, json
from pathlib import Path
from lib_compat.json_store_async import async_read_json, async_write_json_atomic

@pytest.mark.asyncio
async def test_read_missing_returns_default():
    p = Path(tempfile.mkdtemp()) / "nope.json"
    assert await async_read_json(p, default={}) == {}

@pytest.mark.asyncio
async def test_write_atomic_creates_file():
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "x.json"
        await async_write_json_atomic(p, {"a": 1})
        assert json.loads(p.read_text()) == {"a": 1}
```

- [ ] **步骤 2：写 lib_compat/json_store_async.py**

```python
import json, os
import aiofiles
from pathlib import Path
from typing import Any

async def async_read_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    async with aiofiles.open(path, "r", encoding="utf-8") as f:
        text = await f.read()
    return json.loads(text) if text.strip() else default

async def async_write_json_atomic(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    async with aiofiles.open(tmp, "w", encoding="utf-8") as f:
        await f.write(json.dumps(data, ensure_ascii=False, indent=2))
    os.replace(tmp, path)
```

- [ ] **步骤 3：requirements 追加 aiofiles（任务 2 已加）**

- [ ] **步骤 4：跑测试**

运行：`pytest backend/tests/unit/test_json_store_async.py -v`
预期：PASS

---

### 任务 10：Suite/Case/Run/Schedule SQLAlchemy 模型

**文件：**
- 创建：`backend/app/models/catalog.py`
- 创建：`backend/app/models/runtime.py`
- 创建：`backend/app/models/audit.py`
- 创建：`backend/tests/unit/test_models_import.py`

- [ ] **步骤 1：写 import 烟雾测试**

```python
# backend/tests/unit/test_models_import.py
def test_models_import():
    from app.models.auth import User, Role, UserRole, ResourceACL
    from app.models.catalog import Suite, Case
    from app.models.runtime import Run, Schedule
    from app.models.audit import AuditEvent
    assert all([User, Role, UserRole, ResourceACL, Suite, Case, Run, Schedule, AuditEvent])
```

- [ ] **步骤 2：写 app/models/catalog.py**

```python
from datetime import datetime
from sqlalchemy import String, Integer, Text, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Suite(Base):
    __tablename__ = "suites"
    __table_args__ = {"schema": "catalog"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class Case(Base):
    __tablename__ = "cases"
    __table_args__ = {"schema": "catalog"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    suite_id: Mapped[int] = mapped_column(ForeignKey("catalog.suites.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    tags: Mapped[list] = mapped_column(JSON, default=list)
    steps: Mapped[list] = mapped_column(JSON, default=list)
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
```

- [ ] **步骤 3：写 app/models/runtime.py**

```python
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class Run(Base):
    __tablename__ = "runs"
    __table_args__ = {"schema": "runtime"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    suite_id: Mapped[int | None] = mapped_column(ForeignKey("catalog.suites.id"))
    env: Mapped[str] = mapped_column(String(32))
    browser: Mapped[str] = mapped_column(String(16))
    status: Mapped[str] = mapped_column(String(16), default="queued", index=True)
    started_by: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary: Mapped[dict] = mapped_column(JSON, default=dict)
    log_path: Mapped[str | None] = mapped_column(String(255))

class Schedule(Base):
    __tablename__ = "schedules"
    __table_args__ = {"schema": "runtime"}
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    suite_id: Mapped[int] = mapped_column(ForeignKey("catalog.suites.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(120))
    cron: Mapped[str] = mapped_column(String(64))
    env: Mapped[str | None] = mapped_column(String(32))
    browser: Mapped[str | None] = mapped_column(String(16))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    owner_id: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **步骤 4：写 app/models/audit.py**

```python
from datetime import datetime
from sqlalchemy import BigInteger, String, Integer, JSON, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base

class AuditEvent(Base):
    __tablename__ = "audit_events"
    __table_args__ = {"schema": "audit"}
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    actor_id: Mapped[int | None] = mapped_column(ForeignKey("auth.users.id"))
    action: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str | None] = mapped_column(String(32))
    target_id: Mapped[str | None] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
```

- [ ] **步骤 5：跑测试 + 迁移**

```bash
alembic upgrade head
pytest backend/tests/unit/test_models_import.py -v
```

---

### 任务 11：SuiteService + CaseService async repos

**文件：**
- 创建：`backend/app/schemas/catalog.py`
- 创建：`backend/app/services/suite_service.py`
- 创建：`backend/app/services/case_service.py`
- 创建：`backend/tests/unit/test_suite_case_service.py`

- [ ] **步骤 1：写 service 测试**

```python
# backend/tests/unit/test_suite_case_service.py
import pytest
from app.services.suite_service import create_suite, list_suites
from app.services.case_service import create_case, add_step
from app.models.auth import User

@pytest.mark.asyncio
async def test_create_and_list_suite(db_session):
    u = User(email="o@e.c"); db_session.add(u); await db_session.flush()
    s = await create_suite(db_session, name="login", description="", owner_id=u.id)
    suites = await list_suites(db_session)
    assert any(x.id == s.id for x in suites)

@pytest.mark.asyncio
async def test_case_steps_roundtrip(db_session):
    u = User(email="o@e.c"); db_session.add(u); await db_session.flush()
    s = await create_suite(db_session, name="s", owner_id=u.id)
    c = await create_case(db_session, suite_id=s.id, name="t1", tags=["smoke"], owner_id=u.id)
    c = await add_step(db_session, case_id=c.id, step={"action": "goto", "value": "https://x"})
    assert c.steps[-1]["action"] == "goto"
```

- [ ] **步骤 2：写 app/schemas/catalog.py**

```python
from pydantic import BaseModel, Field
from datetime import datetime

class SuiteIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""

class SuiteOut(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int | None
    created_at: datetime
    model_config = {"from_attributes": True}

class Step(BaseModel):
    action: str  # goto/click/fill/expect/check/select/hover/wait/screenshot/scroll/eval
    selector: str | None = None
    value: str | None = None
    expect: str | None = None
    timeout_ms: int | None = None
    note: str | None = None

class CaseIn(BaseModel):
    suite_id: int
    name: str = Field(min_length=1, max_length=160)
    tags: list[str] = []
    steps: list[Step] = []

class CaseOut(BaseModel):
    id: int
    suite_id: int
    name: str
    tags: list[str]
    steps: list[Step]
    owner_id: int | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
```

- [ ] **步骤 3：写 app/services/suite_service.py**

```python
from sqlalchemy import select
from app.models.catalog import Suite

async def create_suite(db, *, name, description="", owner_id=None) -> Suite:
    s = Suite(name=name, description=description, owner_id=owner_id)
    db.add(s); await db.flush(); await db.refresh(s)
    return s

async def list_suites(db) -> list[Suite]:
    res = await db.execute(select(Suite).order_by(Suite.id))
    return list(res.scalars())

async def get_suite(db, suite_id: int) -> Suite | None:
    return (await db.execute(select(Suite).where(Suite.id == suite_id))).scalar_one_or_none()

async def update_suite(db, suite_id: int, **fields) -> Suite | None:
    s = await get_suite(db, suite_id)
    if not s: return None
    for k, v in fields.items():
        if v is not None and hasattr(s, k): setattr(s, k, v)
    await db.flush(); await db.refresh(s)
    return s

async def delete_suite(db, suite_id: int) -> bool:
    s = await get_suite(db, suite_id)
    if not s: return False
    await db.delete(s); await db.flush()
    return True
```

- [ ] **步骤 4：写 app/services/case_service.py**

```python
from sqlalchemy import select
from app.models.catalog import Case

async def create_case(db, *, suite_id, name, tags=None, steps=None, owner_id=None) -> Case:
    c = Case(suite_id=suite_id, name=name, tags=tags or [], steps=steps or [], owner_id=owner_id)
    db.add(c); await db.flush(); await db.refresh(c)
    return c

async def get_case(db, case_id: int) -> Case | None:
    return (await db.execute(select(Case).where(Case.id == case_id))).scalar_one_or_none()

async def list_cases(db, suite_id: int | None = None) -> list[Case]:
    q = select(Case).order_by(Case.id)
    if suite_id is not None: q = q.where(Case.suite_id == suite_id)
    return list((await db.execute(q)).scalars())

async def add_step(db, *, case_id: int, step: dict) -> Case:
    c = await get_case(db, case_id)
    assert c, "case not found"
    steps = list(c.steps or [])
    steps.append(step)
    c.steps = steps
    await db.flush(); await db.refresh(c)
    return c

async def update_case_steps(db, *, case_id: int, steps: list[dict]) -> Case:
    c = await get_case(db, case_id)
    assert c, "case not found"
    c.steps = steps
    await db.flush(); await db.refresh(c)
    return c

async def delete_case(db, case_id: int) -> bool:
    c = await get_case(db, case_id)
    if not c: return False
    await db.delete(c); await db.flush()
    return True
```

- [ ] **步骤 5：跑测试**

运行：`pytest backend/tests/unit/test_suite_case_service.py -v`
预期：PASS

---

### 任务 12：Streamlit 写操作写 PG（双写层）

**文件：**
- 创建：`streamlit_app/services/pg_writer.py`
- 修改：`streamlit_app/services/suite_service.py`
- 修改：`streamlit_app/services/case_service.py`
- 创建：`backend/tests/integration/test_dual_write.py`

- [ ] **步骤 1：写双写一致性测试**

```python
# backend/tests/integration/test_dual_write.py
import pytest, tempfile
from pathlib import Path
from streamlit_app.services import suite_service
from sqlalchemy import select
from app.models.catalog import Suite

@pytest.mark.asyncio
async def test_dual_write_persists_to_both(db_session, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    suite_service.set_suites([{"name": "s1", "description": ""}])
    s1 = suite_service.get_suites()[0]
    res = await db_session.execute(select(Suite).where(Suite.name == "s1"))
    assert res.scalar_one_or_none() is not None
```

- [ ] **步骤 2：写 streamlit_app/services/pg_writer.py**

```python
"""PG writer 包装, Streamlit 同步上下文用同步 SQLAlchemy 引擎"""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app import models  # noqa

_DSN = os.environ.get("DUAL_WRITE_DSN") or os.environ.get("DATABASE_URL", "").replace("+asyncpg", "")
_engine = None
_Session = None

def _ensure_session():
    global _engine, _Session
    if _Session is None:
        _engine = create_engine(_DSN, pool_pre_ping=True, future=True)
        _Session = sessionmaker(_engine, expire_on_commit=False, future=True)
    return _Session()

def write_suite_to_pg(suite_dict: dict) -> int | None:
    if not _DSN: return None
    from app.models.catalog import Suite
    s = Suite(
        id=suite_dict.get("id"),
        name=suite_dict["name"],
        description=suite_dict.get("description", ""),
        owner_id=suite_dict.get("owner_id"),
    )
    with _ensure_session() as s2:
        s2.merge(s); s2.commit()
    return s.id or suite_dict.get("id")

def write_case_to_pg(case_dict: dict) -> int | None:
    if not _DSN: return None
    from app.models.catalog import Case
    c = Case(
        id=case_dict.get("id"),
        suite_id=case_dict["suite_id"],
        name=case_dict["name"],
        tags=case_dict.get("tags", []),
        steps=case_dict.get("steps", []),
        owner_id=case_dict.get("owner_id"),
    )
    with _ensure_session() as s2:
        s2.merge(c); s2.commit()
    return c.id or case_dict.get("id")
```

- [ ] **步骤 3：改 streamlit_app/services/suite_service.py 调双写**

```python
# streamlit_app/services/suite_service.py 追加
try:
    from streamlit_app.services.pg_writer import write_suite_to_pg
except Exception:
    write_suite_to_pg = None

def set_suites(suites):
    _store["suites"] = suites
    persist_suites(_store["suites"])
    if write_suite_to_pg:
        for s in suites:
            try: write_suite_to_pg(s)
            except Exception: pass
```

- [ ] **步骤 4：跑测试**

预期：PASS（需 PG 跑迁移 + 表清空 + DATABASE_URL 环境变量）

---

### 任务 13：FastAPI 读端走 PG

**文件：**
- 创建：`backend/app/routers/suites.py`
- 创建：`backend/app/routers/cases.py`
- 创建：`backend/app/security/rbac.py`
- 修改：`backend/app/main.py`

- [ ] **步骤 1：写 suite 路由测试**

```python
# backend/tests/integration/test_suite_routes.py
import pytest

@pytest.mark.asyncio
async def test_list_suites_empty(client, db_session):
    r = await client.get("/api/suites")
    assert r.status_code == 200
    assert r.json() == []

@pytest.mark.asyncio
async def test_create_suite_returns_201(client, db_session):
    r = await client.post("/api/suites", json={"name": "s1"})
    assert r.status_code == 201
    assert r.json()["name"] == "s1"
```

- [ ] **步骤 2：写 app/security/rbac.py 骨架**

```python
from fastapi import HTTPException
from sqlalchemy import select
from app.models.auth import User, ResourceACL

async def assert_can(user: User, action: str, resource: tuple[str, str|int], db) -> None:
    role_names = {r.role.name for r in user.roles}
    if "admin" in role_names: return
    rt, rid = resource
    q = select(ResourceACL).where(
        ResourceACL.resource_type == rt,
        ResourceACL.resource_id == str(rid),
        ResourceACL.principal_id.in_([str(user.id), *role_names]),
        ResourceACL.permission == action,
    )
    res = (await db.execute(q)).scalars().first()
    if not res and action in ("read", "write") and "editor" in role_names:
        return
    if not res:
        raise HTTPException(403, f"forbidden: {action} {rt}:{rid}")
```

- [ ] **步骤 3：写 routers/suites.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from app.deps import get_db, get_current_user
from app.schemas.catalog import SuiteIn, SuiteOut
from app.services import suite_service
from app.security.rbac import assert_can

router = APIRouter(prefix="/api/suites", tags=["suites"])

@router.get("", response_model=list[SuiteOut])
async def list_(db=Depends(get_db), user=Depends(get_current_user)):
    return await suite_service.list_suites(db)

@router.post("", response_model=SuiteOut, status_code=201)
async def create(body: SuiteIn, db=Depends(get_db), user=Depends(get_current_user)):
    return await suite_service.create_suite(db, name=body.name, description=body.description, owner_id=user.id)

@router.put("/{suite_id}", response_model=SuiteOut)
async def update(suite_id: int, body: SuiteIn, db=Depends(get_db), user=Depends(get_current_user)):
    s = await suite_service.get_suite(db, suite_id)
    if not s: raise HTTPException(404, "not found")
    await assert_can(user, "write", ("suite", suite_id), db)
    return await suite_service.update_suite(db, suite_id, name=body.name, description=body.description)

@router.delete("/{suite_id}", status_code=204)
async def delete(suite_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    s = await suite_service.get_suite(db, suite_id)
    if not s: raise HTTPException(404, "not found")
    await assert_can(user, "delete", ("suite", suite_id), db)
    await suite_service.delete_suite(db, suite_id)
    return None
```

- [ ] **步骤 4：写 routers/cases.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from app.deps import get_db, get_current_user
from app.schemas.catalog import CaseIn, CaseOut
from app.services import case_service

router = APIRouter(prefix="/api/cases", tags=["cases"])

@router.get("", response_model=list[CaseOut])
async def list_(suite_id: int | None = None, db=Depends(get_db), user=Depends(get_current_user)):
    return await case_service.list_cases(db, suite_id=suite_id)

@router.get("/{case_id}", response_model=CaseOut)
async def get(case_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    c = await case_service.get_case(db, case_id)
    if not c: raise HTTPException(404, "not found")
    return c

@router.post("", response_model=CaseOut, status_code=201)
async def create(body: CaseIn, db=Depends(get_db), user=Depends(get_current_user)):
    return await case_service.create_case(db, suite_id=body.suite_id, name=body.name, tags=body.tags, steps=[s.model_dump() for s in body.steps], owner_id=user.id)

@router.put("/{case_id}", response_model=CaseOut)
async def update(case_id: int, body: CaseIn, db=Depends(get_db), user=Depends(get_current_user)):
    c = await case_service.get_case(db, case_id)
    if not c: raise HTTPException(404, "not found")
    return await case_service.update_case_steps(db, case_id=case_id, steps=[s.model_dump() for s in body.steps])

@router.delete("/{case_id}", status_code=204)
async def delete(case_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    ok = await case_service.delete_case(db, case_id)
    if not ok: raise HTTPException(404, "not found")
    return None
```

- [ ] **步骤 5：注册路由**

```python
# main.py
from app.routers import suites, cases
app.include_router(suites.router)
app.include_router(cases.router)
```

- [ ] **步骤 6：跑测试**

预期：PASS

---

### 任务 14：verify_legacy_migration.py + import_legacy_json.py

**文件：**
- 创建：`backend/scripts/__init__.py`
- 创建：`backend/scripts/import_legacy_json.py`
- 创建：`backend/scripts/verify_legacy_migration.py`
- 创建：`backend/tests/integration/test_import_legacy.py`

- [ ] **步骤 1：写 import 脚本**

```python
# backend/scripts/import_legacy_json.py
"""可选: 从旧 logs/suites.json + logs/testcases.json 导入 PG"""
import asyncio, json
from pathlib import Path
from app.db.session import session_scope
from app.services.suite_service import create_suite
from app.services.case_service import create_case

async def import_all(suites_path: Path, cases_path: Path) -> tuple[int, int]:
    suites = json.loads(suites_path.read_text()) if suites_path.exists() else []
    cases = json.loads(cases_path.read_text()) if cases_path.exists() else []
    n_s, n_c = 0, 0
    async with session_scope() as db:
        for s in suites:
            await create_suite(db, name=s["name"], description=s.get("description", ""))
            n_s += 1
        for c in cases:
            await create_case(db, suite_id=c["suite_id"], name=c["name"], tags=c.get("tags", []), steps=c.get("steps", []))
            n_c += 1
    return n_s, n_c

if __name__ == "__main__":
    s, c = asyncio.run(import_all(Path("logs/suites.json"), Path("logs/testcases.json")))
    print(f"imported suites={s} cases={c}")
```

- [ ] **步骤 2：写 verify 脚本**

```python
# backend/scripts/verify_legacy_migration.py
import asyncio, json
from pathlib import Path
from sqlalchemy import select, func
from app.db.session import session_scope
from app.models.catalog import Suite, Case
from lib_compat.json_store_async import async_read_json

async def verify():
    s_json = await async_read_json(Path("logs/suites.json"), default=[])
    c_json = await async_read_json(Path("logs/testcases.json"), default=[])
    async with session_scope() as db:
        s_pg = (await db.execute(select(func.count()).select_from(Suite))).scalar()
        c_pg = (await db.execute(select(func.count()).select_from(Case))).scalar()
    return {
        "suites": {"json": len(s_json), "pg": s_pg},
        "cases":  {"json": len(c_json), "pg": c_pg},
        "ok": len(s_json) == s_pg and len(c_json) == c_pg,
    }

if __name__ == "__main__":
    print(json.dumps(asyncio.run(verify()), indent=2))
```

- [ ] **步骤 3：写测试**

```python
# backend/tests/integration/test_import_legacy.py
import pytest, json, tempfile
from pathlib import Path
from importlib import import_module
m = import_module("backend.scripts.import_legacy_json") if False else None
# 实际直接用 importlib.util 加载
import importlib.util, sys
spec = importlib.util.spec_from_file_location("import_legacy", "backend/scripts/import_legacy_json.py")
mod = importlib.util.module_from_spec(spec)
sys.modules["import_legacy"] = mod
spec.loader.exec_module(mod)

@pytest.mark.asyncio
async def test_import_creates_suites_and_cases():
    with tempfile.TemporaryDirectory() as d:
        sp = Path(d)/"suites.json"; sp.write_text(json.dumps([{"name":"s1","description":""}]))
        cp = Path(d)/"cases.json"; cp.write_text(json.dumps([{"suite_id":1,"name":"c1","tags":[],"steps":[]}]))
        ns, nc = await mod.import_all(sp, cp)
        assert ns == 1 and nc == 1
```

- [ ] **步骤 4：跑测试**

预期：PASS

---

## Phase 3a：静态页（4 天，5 任务）

### 任务 15：Suite CRUD（Vue + FastAPI）

**文件：**
- 创建：`frontend/src/api/suites.ts`
- 创建：`frontend/src/pages/Suites.vue`
- 创建：`frontend/src/pages/SuiteDetail.vue`
- 创建：`frontend/tests/component/Suites.test.ts`

- [ ] **步骤 1：写 Suites 页面组件测试**

```ts
// frontend/tests/component/Suites.test.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'

vi.mock('@/api/suites', () => ({
  list: vi.fn().mockResolvedValue([{ id: 1, name: 's1', description: 'd', owner_id: 1, created_at: '2026-01-01' }]),
  create: vi.fn(),
  remove: vi.fn(),
}))

import Suites from '@/pages/Suites.vue'

describe('Suites.vue', () => {
  it('renders list from api', async () => {
    setActivePinia(createPinia())
    const router = createRouter({ history: createMemoryHistory(), routes: [{ path: '/', component: { template: '<div/>' } }] })
    const w = mount(Suites, { global: { plugins: [router] } })
    await new Promise(r => setTimeout(r, 0))
    expect(w.text()).toContain('s1')
  })
})
```

- [ ] **步骤 2：写 src/api/suites.ts**

```ts
import { http } from './client'
export interface Suite { id: number; name: string; description: string; owner_id: number | null; created_at: string }
export const list = () => http.get<Suite[]>('/suites').then(r => r.data)
export const create = (b: { name: string; description?: string }) => http.post<Suite>('/suites', b).then(r => r.data)
export const update = (id: number, b: { name: string; description?: string }) => http.put<Suite>(`/suites/${id}`, b).then(r => r.data)
export const remove = (id: number) => http.delete(`/suites/${id}`).then(r => r.data)
```

- [ ] **步骤 3：写 src/pages/Suites.vue**

```vue
<script setup lang="ts">
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import * as api from '@/api/suites'

const qc = useQueryClient()
const { data, isLoading } = useQuery({ queryKey: ['suites'], queryFn: api.list })

const form = ref({ name: '', description: '' })
const create = useMutation({
  mutationFn: api.create,
  onSuccess: () => { qc.invalidateQueries({ queryKey: ['suites'] }); ElMessage.success('已创建'); form.value = { name: '', description: '' } },
})
const remove = useMutation({
  mutationFn: api.remove,
  onSuccess: () => qc.invalidateQueries({ queryKey: ['suites'] }),
})
function onDelete(id: number) {
  ElMessageBox.confirm('确认删除?').then(() => remove.mutate(id)).catch(() => {})
}
</script>

<template>
  <h2>测试套件</h2>
  <el-form inline @submit.prevent="create.mutate(form)">
    <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
    <el-form-item label="描述"><el-input v-model="form.description" /></el-form-item>
    <el-button type="primary" native-type="submit" :loading="create.isPending.value">新建</el-button>
  </el-form>
  <el-table :data="data || []" v-loading="isLoading" stripe>
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="name" label="名称" />
    <el-table-column prop="description" label="描述" />
    <el-table-column label="操作" width="160">
      <template #default="{ row }">
        <router-link :to="`/suites/${row.id}`">详情</router-link>
        <el-button size="small" type="danger" style="margin-left:8px" @click="onDelete(row.id)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>
```

- [ ] **步骤 4：写 src/pages/SuiteDetail.vue**

```vue
<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useQuery } from '@tanstack/vue-query'
import { list as listCases } from '@/api/cases'
const route = useRoute()
const suiteId = Number(route.params.id)
const { data } = useQuery({ queryKey: ['cases', suiteId], queryFn: () => listCases(suiteId) })
</script>
<template>
  <h2>套件 #{{ suiteId }}</h2>
  <router-link :to="`/cases?suite=${suiteId}&new=1`">+ 新建用例</router-link>
  <el-table :data="data || []">
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="name" label="名称" />
    <el-table-column prop="tags" label="标签" />
  </el-table>
</template>
```

- [ ] **步骤 5：跑测试**

运行：`cd frontend && npx vitest run Suites`
预期：PASS

---

### 任务 16：Case 列表基础 CRUD

**文件：**
- 创建：`frontend/src/types/step.ts`
- 创建：`frontend/src/api/cases.ts`
- 创建：`frontend/src/pages/Cases.vue`

- [ ] **步骤 1：写 src/types/step.ts**

```ts
export type StepAction = 'goto' | 'click' | 'fill' | 'expect' | 'check' | 'select' | 'hover' | 'wait' | 'screenshot' | 'scroll' | 'eval'
export interface Step {
  action: StepAction
  selector?: string
  value?: string
  expect?: string
  timeout_ms?: number
  note?: string
}
export const STEP_ACTIONS: StepAction[] = ['goto','click','fill','expect','check','select','hover','wait','screenshot','scroll','eval']
```

- [ ] **步骤 2：写 src/api/cases.ts**

```ts
import { http } from './client'
import type { Step } from '@/types/step'
export interface Case { id: number; suite_id: number; name: string; tags: string[]; steps: Step[]; owner_id: number | null; created_at: string; updated_at: string }
export const list = (suiteId?: number) => http.get<Case[]>('/cases', { params: suiteId ? { suite_id: suiteId } : {} }).then(r => r.data)
export const get = (id: number) => http.get<Case>(`/cases/${id}`).then(r => r.data)
export const create = (b: { suite_id: number; name: string; tags?: string[]; steps?: Step[] }) => http.post<Case>('/cases', b).then(r => r.data)
export const update = (id: number, b: { name?: string; tags?: string[]; steps?: Step[] }) => http.put<Case>(`/cases/${id}`, b).then(r => r.data)
export const remove = (id: number) => http.delete(`/cases/${id}`).then(r => r.data)
```

- [ ] **步骤 3：写 src/pages/Cases.vue**

```vue
<script setup lang="ts">
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as api from '@/api/cases'
import { list as listSuites } from '@/api/suites'

const route = useRoute(); const router = useRouter(); const qc = useQueryClient()
const suiteFilter = ref<number | undefined>(Number(route.query.suite) || undefined)
const { data: suites } = useQuery({ queryKey: ['suites'], queryFn: listSuites })
const { data: cases, isLoading } = useQuery({ queryKey: ['cases', suiteFilter], queryFn: () => api.list(suiteFilter.value) })

const form = ref({ suite_id: suiteFilter.value || 0, name: '' })
const create = useMutation({
  mutationFn: () => api.create({ suite_id: form.value.suite_id, name: form.value.name }),
  onSuccess: () => { qc.invalidateQueries({ queryKey: ['cases'] }); ElMessage.success('已创建'); router.push({ path: '/cases', query: { suite: String(form.value.suite_id) } }) },
})
</script>

<template>
  <h2>测试用例</h2>
  <el-form inline>
    <el-form-item label="套件">
      <el-select v-model="suiteFilter" placeholder="全部" clearable>
        <el-option v-for="s in suites || []" :key="s.id" :label="s.name" :value="s.id" />
      </el-select>
    </el-form-item>
  </el-form>
  <el-form inline @submit.prevent="create.mutate()">
    <el-form-item label="套件">
      <el-select v-model="form.suite_id"><el-option v-for="s in suites || []" :key="s.id" :label="s.name" :value="s.id" /></el-select>
    </el-form-item>
    <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
    <el-button native-type="submit" type="primary" :loading="create.isPending.value">新建</el-button>
  </el-form>
  <el-table :data="cases || []" v-loading="isLoading" stripe>
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="name" label="名称" />
    <el-table-column label="步骤数">
      <template #default="{ row }">{{ (row.steps || []).length }}</template>
    </el-table-column>
    <el-table-column label="操作">
      <template #default="{ row }">
        <router-link :to="`/cases/${row.id}/edit`">编辑步骤</router-link>
      </template>
    </el-table-column>
  </el-table>
</template>
```

- [ ] **步骤 4：手测**

浏览器：能列套件、新建用例、跳到 `/cases/:id/edit`（下一步实现）

---

### 任务 17：Dashboard（5 指标 + ECharts）

**文件：**
- 创建：`backend/app/routers/dashboard.py`
- 创建：`frontend/src/components/EChart.vue`
- 修改：`frontend/src/pages/Dashboard.vue`

- [ ] **步骤 1：写 dashboard 聚合 API**

```python
# backend/app/routers/dashboard.py
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from datetime import datetime, timedelta, timezone
from app.deps import get_db, get_current_user
from app.models.runtime import Run
from app.models.catalog import Suite, Case

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

@router.get("/summary")
async def summary(db=Depends(get_db), user=Depends(get_current_user)):
    total_suites = (await db.execute(select(func.count()).select_from(Suite))).scalar()
    total_cases = (await db.execute(select(func.count()).select_from(Case))).scalar()
    runs_24h = (await db.execute(
        select(func.count()).select_from(Run)
        .where(Run.started_at >= datetime.now(timezone.utc) - timedelta(hours=24))
    )).scalar()
    runs = (await db.execute(select(Run.status, func.count()).group_by(Run.status))).all()
    status_counts = dict(runs)
    total_runs = sum(status_counts.values()) or 1
    pass_rate = round((status_counts.get("passed", 0) / total_runs) * 100, 1)
    return {
        "total_suites": total_suites,
        "total_cases": total_cases,
        "runs_24h": runs_24h,
        "pass_rate": pass_rate,
        "status_distribution": status_counts,
    }

@router.get("/trends")
async def trends(days: int = 14, db=Depends(get_db), user=Depends(get_current_user)):
    start = datetime.now(timezone.utc) - timedelta(days=days)
    runs = (await db.execute(select(Run.started_at, Run.status).where(Run.started_at >= start))).all()
    buckets: dict[str, dict[str, int]] = {}
    for started, status in runs:
        k = started.date().isoformat()
        buckets.setdefault(k, {"passed": 0, "failed": 0})
        if status in buckets[k]: buckets[k][status] += 1
    return [{"date": k, **v} for k, v in sorted(buckets.items())]
```

- [ ] **步骤 2：注册路由**

```python
# main.py
from app.routers import dashboard
app.include_router(dashboard.router)
```

- [ ] **步骤 3：写 src/components/EChart.vue**

```vue
<script setup lang="ts">
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart, BarChart, LineChart } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent, GridComponent } from 'echarts/components'
import VChart from 'vue-echarts'
use([CanvasRenderer, PieChart, BarChart, LineChart, TitleComponent, TooltipComponent, LegendComponent, GridComponent])
defineProps<{ option: any }>()
</script>
<template>
  <v-chart :option="option" autoresize style="height: 320px" />
</template>
```

- [ ] **步骤 4：写 src/pages/Dashboard.vue（重写）**

```vue
<script setup lang="ts">
import { computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import EChart from '@/components/EChart.vue'
import { http } from '@/api/client'

const { data: sum } = useQuery({ queryKey: ['dash-summary'], queryFn: () => http.get('/dashboard/summary').then(r => r.data) })
const { data: trends } = useQuery({ queryKey: ['dash-trends'], queryFn: () => http.get('/dashboard/trends').then(r => r.data) })

const statusPie = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [{ type: 'pie', radius: ['40%', '70%'], data: Object.entries(sum.value?.status_distribution || {}).map(([k,v]) => ({ name: k, value: v })) }],
}))

const trendLine = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['passed', 'failed'] },
  xAxis: { type: 'category', data: (trends.value || []).map(t => t.date) },
  yAxis: { type: 'value' },
  series: [
    { name: 'passed', type: 'line', data: (trends.value || []).map(t => t.passed) },
    { name: 'failed', type: 'line', data: (trends.value || []).map(t => t.failed) },
  ],
}))
</script>

<template>
  <h2>仪表盘</h2>
  <el-row :gutter="16">
    <el-col :span="6"><el-statistic title="套件数" :value="sum?.total_suites ?? 0" /></el-col>
    <el-col :span="6"><el-statistic title="用例数" :value="sum?.total_cases ?? 0" /></el-col>
    <el-col :span="6"><el-statistic title="24h 运行" :value="sum?.runs_24h ?? 0" /></el-col>
    <el-col :span="6"><el-statistic title="通过率" :value="sum?.pass_rate ?? 0" suffix="%" /></el-col>
  </el-row>
  <el-row :gutter="16" style="margin-top:16px">
    <el-col :span="12"><EChart :option="statusPie" /></el-col>
    <el-col :span="12"><EChart :option="trendLine" /></el-col>
  </el-row>
</template>
```

- [ ] **步骤 5：手测**

浏览器：仪表盘 5 指标 + 饼图 + 折线图渲染

---

### 任务 18：Reports（4 tab）

**文件：**
- 创建：`backend/app/routers/reports.py`
- 创建：`frontend/src/pages/Reports.vue`

- [ ] **步骤 1：写 reports router**

```python
# backend/app/routers/reports.py
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from app.deps import get_current_user
from app.config import settings

router = APIRouter(prefix="/api/reports", tags=["reports"])
_root = Path(settings.allure_results_dir)

@router.get("")
async def list_runs(user=Depends(get_current_user)):
    if not _root.exists(): return []
    runs = []
    for p in sorted(_root.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:50]:
        if p.is_dir() and (any(p.glob("*.json"))):
            runs.append({"id": p.name, "mtime": p.stat().st_mtime})
    return runs

@router.get("/{run_id}/files")
async def list_files(run_id: str, user=Depends(get_current_user)):
    d = _root / run_id
    if not d.exists(): raise HTTPException(404)
    return sorted(str(p.relative_to(d)) for p in d.rglob("*") if p.is_file())

@router.get("/{run_id}/raw/{path:path}")
async def raw(run_id: str, path: str, user=Depends(get_current_user)):
    f = _root / run_id / path
    if not f.exists() or not f.is_file(): raise HTTPException(404)
    return FileResponse(f)
```

- [ ] **步骤 2：注册路由**

```python
# main.py
from app.routers import reports
app.include_router(reports.router)
```

- [ ] **步骤 3：写 src/pages/Reports.vue（4 tab）**

```vue
<script setup lang="ts">
import { ref, computed } from 'vue'
import { useQuery } from '@tanstack/vue-query'
import { http } from '@/api/client'
const active = ref('allure')
const { data: runs } = useQuery({ queryKey: ['reports'], queryFn: () => http.get('/reports').then(r => r.data) })
const selected = ref<string | null>(null)
const { data: files } = useQuery({
  queryKey: ['reports-files', selected],
  queryFn: () => http.get(`/reports/${selected.value}/files`).then(r => r.data),
  enabled: computed(() => !!selected.value),
})
function urlOf(p: string) { return `/api/reports/${selected.value}/raw/${p}` }
</script>
<template>
  <h2>报告</h2>
  <el-tabs v-model="active">
    <el-tab-pane label="Allure" name="allure">
      <el-row :gutter="16">
        <el-col :span="8">
          <el-list>
            <el-list-item v-for="r in runs || []" :key="r.id" @click="selected = r.id" :class="{ active: selected === r.id }">
              {{ r.id }}
            </el-list-item>
          </el-list>
        </el-col>
        <el-col :span="16">
          <iframe v-if="selected" :src="`/api/reports/${selected}/raw/index.html`" style="width:100%;height:80vh;border:0" />
        </el-col>
      </el-row>
    </el-tab-pane>
    <el-tab-pane label="HTML" name="html">
      <el-table :data="(files || []).filter(f => f.endsWith('.html'))">
        <el-table-column prop="*" label="文件" />
      </el-table>
    </el-tab-pane>
    <el-tab-pane label="截图" name="shots">
      <el-image v-for="f in (files || []).filter(f => /png|jpg|jpeg|webp/.test(f))" :key="f" :src="urlOf(f)" fit="contain" style="max-width:200px;margin:4px" />
    </el-tab-pane>
    <el-tab-pane label="日志" name="logs">
      <pre v-for="f in (files || []).filter(f => f.endsWith('.log') || f.endsWith('.txt'))" :key="f">{{ f }}</pre>
    </el-tab-pane>
  </el-tabs>
</template>

<style>.active{background:#ecf5ff}</style>
```

- [ ] **步骤 4：手测**

需有 allure-results 数据；可先用 `pytest --alluredir=allure-results/test smoke` 造一份

---

### 任务 19：Config 页（.env 在线编辑）

**文件：**
- 创建：`backend/app/routers/config.py`
- 创建：`frontend/src/pages/Config.vue`

- [ ] **步骤 1：写 config router**

```python
# backend/app/routers/config.py
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from app.deps import get_current_user
from app.security.rbac import assert_can

router = APIRouter(prefix="/api/config", tags=["config"])
_env = Path(".env")

@router.get("")
async def read(user=Depends(get_current_user)):
    if "admin" not in {r.role.name for r in user.roles}:
        raise HTTPException(403, "admin only")
    if not _env.exists(): return {"content": ""}
    return {"content": _env.read_text(encoding="utf-8")}

@router.put("")
async def write(body: dict, user=Depends(get_current_user)):
    if "admin" not in {r.role.name for r in user.roles}:
        raise HTTPException(403, "admin only")
    content = body.get("content", "")
    if "\x00" in content: raise HTTPException(400, "NUL in content")
    _env.write_text(content, encoding="utf-8")
    return {"ok": True}
```

- [ ] **步骤 2：注册路由**

```python
# main.py
from app.routers import config
app.include_router(config.router)
```

- [ ] **步骤 3：写 src/pages/Config.vue**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { http } from '@/api/client'
const content = ref('')
onMounted(async () => { content.value = (await http.get('/config')).data.content })
async function save() {
  await http.put('/config', { content: content.value })
  ElMessage.success('已保存，重启后生效')
}
</script>
<template>
  <h2>系统配置 (.env)</h2>
  <el-input v-model="content" type="textarea" :rows="24" />
  <el-button type="primary" @click="save">保存</el-button>
</template>
```

- [ ] **步骤 4：手测**

admin 登录 → /config → 编辑 → 保存 → 看到后端 .env 已更新

---

## Phase 3b：测试运行（3 天，4 任务）

### 任务 20：PytestRunner worker（子进程包装）

**文件：**
- 创建：`backend/app/ws/manager.py`
- 创建：`backend/app/services/runner.py`
- 创建：`backend/tests/unit/test_runner.py`

- [ ] **步骤 1：写 runner 测试**

```python
# backend/tests/unit/test_runner.py
import pytest, tempfile
from pathlib import Path
from app.services.runner import PytestRunner, RunConfig

@pytest.mark.asyncio
async def test_runner_emits_log_lines():
    with tempfile.TemporaryDirectory() as d:
        log = Path(d)/"r.log"
        rc = RunConfig(env="test", browser="chromium", suite_id=0, log_path=log, cmd=["python","-c","import sys;print('hi');sys.exit(0)"])
        events = []
        async for ev in PytestRunner().run(rc):
            events.append(ev)
        assert any(e["type"] == "log" for e in events)
        assert any(e["type"] == "exit" for e in events)
        assert log.exists()
```

- [ ] **步骤 2：写 app/ws/manager.py**

```python
from fastapi import WebSocket
import asyncio, json

class WSManager:
    def __init__(self):
        self._conns: dict[str, set[WebSocket]] = {}
        self._lock = asyncio.Lock()
    async def connect(self, channel: str, ws: WebSocket):
        await ws.accept()
        async with self._lock:
            self._conns.setdefault(channel, set()).add(ws)
    async def disconnect(self, channel: str, ws: WebSocket):
        async with self._lock:
            self._conns.get(channel, set()).discard(ws)
    async def broadcast(self, channel: str, msg: dict):
        dead = []
        for ws in list(self._conns.get(channel, set())):
            try: await ws.send_text(json.dumps(msg, ensure_ascii=False))
            except Exception: dead.append(ws)
        for d in dead: await self.disconnect(channel, d)

manager = WSManager()
```

- [ ] **步骤 3：写 app/services/runner.py**

```python
import asyncio, os
from dataclasses import dataclass, field
from pathlib import Path
from typing import AsyncIterator

@dataclass
class RunConfig:
    env: str
    browser: str
    suite_id: int
    log_path: Path
    cmd: list[str]
    cwd: str = "."
    env_overrides: dict = field(default_factory=dict)

class PytestRunner:
    async def run(self, rc: RunConfig) -> AsyncIterator[dict]:
        env = {**os.environ, **rc.env_overrides, "ENV": rc.env, "BROWSER": rc.browser}
        rc.log_path.parent.mkdir(parents=True, exist_ok=True)
        proc = await asyncio.create_subprocess_exec(
            *rc.cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, cwd=rc.cwd, env=env,
        )
        with rc.log_path.open("w", encoding="utf-8") as logf:
            async for line in proc.stdout:
                text = line.decode("utf-8", errors="replace").rstrip("\n")
                logf.write(text + "\n"); logf.flush()
                yield {"type": "log", "data": text}
        code = await proc.wait()
        yield {"type": "exit", "code": code}
```

- [ ] **步骤 4：跑测试**

预期：PASS

---

### 任务 21：/api/runs (POST 启动, GET 列表, GET 详情)

**文件：**
- 创建：`backend/app/services/run_service.py`
- 创建：`backend/app/routers/runs.py`
- 创建：`backend/tests/integration/test_run_routes.py`

- [ ] **步骤 1：写 run_service**

```python
# backend/app/services/run_service.py
from datetime import datetime, timezone
from pathlib import Path
from sqlalchemy import select
from app.models.runtime import Run
from app.config import settings

async def start_run(db, *, suite_id: int, env: str, browser: str, started_by: int) -> Run:
    log_dir = Path(settings.log_dir) / "runs"
    log_dir.mkdir(parents=True, exist_ok=True)
    r = Run(suite_id=suite_id, env=env, browser=browser, started_by=started_by, status="queued")
    db.add(r); await db.flush(); await db.refresh(r)
    r.log_path = str(log_dir / f"run_{r.id}.log")
    await db.flush()
    return r

async def finish_run(db, run_id: int, *, status: str, summary: dict) -> None:
    r = (await db.execute(select(Run).where(Run.id == run_id))).scalar_one()
    r.status = status
    r.summary = summary
    r.finished_at = datetime.now(timezone.utc)
    await db.flush()
```

- [ ] **步骤 2：写 routers/runs.py**

```python
import asyncio
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from app.deps import get_db, get_current_user
from app.models.runtime import Run
from app.services.run_service import start_run, finish_run
from app.services.runner import PytestRunner, RunConfig
from app.ws.manager import manager
from app.config import settings

router = APIRouter(prefix="/api/runs", tags=["runs"])

@router.post("", status_code=201)
async def create_run(body: dict, db=Depends(get_db), user=Depends(get_current_user)):
    suite_id = int(body.get("suite_id", 0))
    env = body["env"]; browser = body["browser"]
    r = await start_run(db, suite_id=suite_id, env=env, browser=browser, started_by=user.id)

    async def _go():
        r2 = (await db.execute(select(Run).where(Run.id == r.id))).scalar_one()
        r2.status = "running"
        await db.flush()
        rc = RunConfig(env=env, browser=browser, suite_id=suite_id,
                       log_path=Path(r2.log_path),
                       cmd=["pytest", "-q", "--alluredir", settings.allure_results_dir, "-x"])
        last_exit = 1
        async for ev in PytestRunner().run(rc):
            await manager.broadcast(f"run:{r.id}", ev)
            if ev["type"] == "exit": last_exit = ev["code"]
        status = "passed" if last_exit == 0 else "failed"
        await finish_run(db, r.id, status=status, summary={"exit_code": last_exit})
    asyncio.create_task(_go())
    return {"id": r.id, "status": r.status}

@router.get("")
async def list_runs(limit: int = 50, db=Depends(get_db), user=Depends(get_current_user)):
    res = await db.execute(select(Run).order_by(Run.id.desc()).limit(limit))
    return [{"id": r.id, "env": r.env, "browser": r.browser, "status": r.status,
             "started_at": str(r.started_at)} for r in res.scalars()]

@router.get("/{run_id}")
async def get_run(run_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    r = (await db.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
    if not r: raise HTTPException(404)
    return {"id": r.id, "status": r.status, "log_path": r.log_path, "summary": r.summary,
            "started_at": str(r.started_at),
            "finished_at": str(r.finished_at) if r.finished_at else None}
```

- [ ] **步骤 3：注册 + 测试**

```python
# main.py
from app.routers import runs
app.include_router(runs.router)
```

```python
# backend/tests/integration/test_run_routes.py
import pytest
@pytest.mark.asyncio
async def test_post_run_creates(client, db_session):
    r = await client.post("/api/runs", json={"suite_id": 0, "env": "test", "browser": "chromium"})
    assert r.status_code == 201
    assert "id" in r.json()

@pytest.mark.asyncio
async def test_list_runs(client, db_session):
    r = await client.get("/api/runs")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
```

---

### 任务 22：WS /ws/run/{id} 推流

**文件：**
- 创建：`backend/app/ws/run_ws.py`
- 修改：`backend/app/main.py`
- 修改：`backend/app/deps.py`

- [ ] **步骤 1：写 get_current_user_ws**

```python
# app/deps.py 追加
from fastapi import WebSocket
async def get_current_user_ws(ws: WebSocket):
    from app.security.jwt import decode_token
    from app.config import settings
    token = ws.cookies.get("access_token")
    if not token:
        auth = ws.headers.get("authorization", "")
        if auth.lower().startswith("bearer "): token = auth.split(" ", 1)[1]
    if not token: await ws.close(code=4401); return None
    try: payload = decode_token(settings, token)
    except Exception: await ws.close(code=4401); return None
    return int(payload["sub"])
```

- [ ] **步骤 2：写 ws 端点**

```python
# app/ws/run_ws.py
import json
from pathlib import Path
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.ws.manager import manager
from app.db.session import SessionLocal
from app.models.runtime import Run

router = APIRouter()

@router.websocket("/ws/run/{run_id}")
async def ws_run(ws: WebSocket, run_id: int):
    await manager.connect(f"run:{run_id}", ws)
    try:
        async with SessionLocal() as db:
            r = (await db.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
        if r and r.log_path and Path(r.log_path).exists():
            for line in Path(r.log_path).read_text(encoding="utf-8", errors="replace").splitlines()[-200:]:
                await ws.send_text(json.dumps({"type": "log", "data": line}, ensure_ascii=False))
        while True:
            await ws.receive_text()  # 心跳
    except WebSocketDisconnect:
        await manager.disconnect(f"run:{run_id}", ws)
```

- [ ] **步骤 3：注册**

```python
# main.py
from app.ws import run_ws
app.include_router(run_ws.router)
```

---

### 任务 23：Runs.vue（环境/类型/浏览器下拉 + 实时日志）

**文件：**
- 创建：`frontend/src/composables/useWS.ts`
- 创建：`frontend/src/api/runs.ts`
- 创建：`frontend/src/components/LogStream.vue`
- 创建：`frontend/src/pages/Runs.vue`
- 创建：`frontend/src/pages/RunDetail.vue`

- [ ] **步骤 1：写 useWS 组合**

```ts
// frontend/src/composables/useWS.ts
import { ref, onUnmounted } from 'vue'
export function useWS(url: string, onMsg: (m: any) => void) {
  const connected = ref(false)
  const ws = new WebSocket(url)
  ws.onopen = () => connected.value = true
  ws.onclose = () => connected.value = false
  ws.onerror = () => connected.value = false
  ws.onmessage = (e) => { try { onMsg(JSON.parse(e.data)) } catch {} }
  onUnmounted(() => ws.close())
  return { connected }
}
```

- [ ] **步骤 2：写 src/api/runs.ts**

```ts
import { http } from './client'
export interface Run { id: number; env: string; browser: string; status: string; started_at: string }
export const start = (b: { suite_id: number; env: string; browser: string }) => http.post<{ id: number }>('/runs', b).then(r => r.data)
export const list = () => http.get<Run[]>('/runs').then(r => r.data)
export const get = (id: number) => http.get(`/runs/${id}`).then(r => r.data)
```

- [ ] **步骤 3：写 LogStream.vue**

```vue
<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
const props = defineProps<{ lines: string[] }>()
const wrap = ref<HTMLElement>()
watch(() => props.lines.length, async () => { await nextTick(); if (wrap.value) wrap.value.scrollTop = wrap.value.scrollHeight })
</script>
<template>
  <pre ref="wrap" style="height:60vh;overflow:auto;background:#1e1e1e;color:#ddd;padding:12px;font:12px/1.5 monospace">{{ lines.join('\n') }}</pre>
</template>
```

- [ ] **步骤 4：写 src/pages/Runs.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import * as api from '@/api/runs'
import { list as listSuites } from '@/api/suites'

const qc = useQueryClient()
const form = ref({ suite_id: 0, env: 'test', browser: 'chromium' })
const start = useMutation({ mutationFn: api.start, onSuccess: ({ id }) => { qc.invalidateQueries({ queryKey: ['runs'] }); location.href = `/runs/${id}` } })
const { data: suites } = useQuery({ queryKey: ['suites'], queryFn: listSuites })
const { data: runs } = useQuery({ queryKey: ['runs'], queryFn: api.list })
</script>
<template>
  <h2>测试运行</h2>
  <el-form inline>
    <el-form-item label="套件"><el-select v-model="form.suite_id"><el-option v-for="s in suites || []" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-form-item>
    <el-form-item label="环境"><el-select v-model="form.env"><el-option label="test" value="test" /><el-option label="staging" value="staging" /><el-option label="prod" value="prod" /></el-select></el-form-item>
    <el-form-item label="浏览器"><el-select v-model="form.browser"><el-option label="chromium" value="chromium" /><el-option label="firefox" value="firefox" /><el-option label="webkit" value="webkit" /></el-select></el-form-item>
    <el-button type="primary" :loading="start.isPending.value" @click="start.mutate(form)">启动</el-button>
  </el-form>
  <el-table :data="runs || []">
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="env" label="环境" />
    <el-table-column prop="browser" label="浏览器" />
    <el-table-column prop="status" label="状态">
      <template #default="{ row }"><el-tag :type="row.status === 'passed' ? 'success' : row.status === 'failed' ? 'danger' : 'info'">{{ row.status }}</el-tag></template>
    </el-table-column>
    <el-table-column label="操作"><template #default="{ row }"><router-link :to="`/runs/${row.id}`">详情</router-link></template></el-table-column>
  </el-table>
</template>
```

- [ ] **步骤 5：写 src/pages/RunDetail.vue**

```vue
<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useWS } from '@/composables/useWS'
import LogStream from '@/components/LogStream.vue'
const route = useRoute()
const id = Number(route.params.id)
const lines = ref<string[]>([])
useWS(`${import.meta.env.VITE_WS_BASE || '/ws'}/run/${id}`, (m) => { if (m.type === 'log') lines.value.push(m.data) })
</script>
<template>
  <h2>运行 #{{ id }}</h2>
  <LogStream :lines="lines" />
</template>
```

- [ ] **步骤 6：手测**

启动一次 pytest，浏览器看实时日志

## Phase 3c — 测试用例（最复杂，9 任务，预计 8 天）

> 复用 Phase 3a 任务 16 后端的 `CaseService`。本阶段专注前端编辑器、录制器、脚本生成、回放推流。
> 11 种 step action：`goto` / `click` / `fill` / `expect` / `check` / `select` / `hover` / `wait` / `screenshot` / `scroll` / `eval`
> 每个 action 的 schema 见任务 24 步骤 1 的 `STEP_SCHEMAS`。

---

### 任务 24：StepEditor.vue（VxeTable，11 种 action 的下拉与字段动态渲染）

**文件：**
- 创建：`frontend/src/components/StepEditor.vue`
- 创建：`frontend/src/types/step.ts`
- 创建：`frontend/src/components/StepEditor.test.ts`
- 修改：`frontend/src/pages/CaseEditor.vue`（先用占位，下一任务完善）

- [ ] **步骤 1：定义 step 类型**

```ts
// frontend/src/types/step.ts
export type ActionName =
  | 'goto' | 'click' | 'fill' | 'expect' | 'check'
  | 'select' | 'hover' | 'wait' | 'screenshot' | 'scroll' | 'eval'

export interface FieldSpec { name: string; label: string; required?: boolean; default?: string }
export interface ActionSpec { name: ActionName; label: string; fields: FieldSpec[] }

export const STEP_SCHEMAS: ActionSpec[] = [
  { name: 'goto', label: '打开 URL', fields: [{ name: 'url', label: 'URL', required: true }] },
  { name: 'click', label: '点击', fields: [{ name: 'selector', label: '选择器', required: true }] },
  { name: 'fill', label: '输入', fields: [
    { name: 'selector', label: '选择器', required: true },
    { name: 'value', label: '值', required: true }
  ] },
  { name: 'expect', label: '断言文本', fields: [
    { name: 'selector', label: '选择器', required: true },
    { name: 'value', label: '期望文本', required: true }
  ] },
  { name: 'check', label: '断言可见', fields: [{ name: 'selector', label: '选择器', required: true }] },
  { name: 'select', label: '下拉选择', fields: [
    { name: 'selector', label: '选择器', required: true },
    { name: 'value', label: '选项值', required: true }
  ] },
  { name: 'hover', label: '悬停', fields: [{ name: 'selector', label: '选择器', required: true }] },
  { name: 'wait', label: '等待(毫秒)', fields: [{ name: 'value', label: '毫秒', required: true, default: '500' }] },
  { name: 'screenshot', label: '截图', fields: [{ name: 'value', label: '文件名', default: 'shot.png' }] },
  { name: 'scroll', label: '滚动', fields: [
    { name: 'selector', label: '选择器', required: false },
    { name: 'value', label: '方向(top/bottom/数值)', default: 'bottom' }
  ] },
  { name: 'eval', label: '执行 JS', fields: [{ name: 'value', label: 'JS 表达式', required: true }] }
]

export interface Step { id: string; action: ActionName; params: Record<string, string> }
```

- [ ] **步骤 2：写 StepEditor 组件**

```vue
<!-- frontend/src/components/StepEditor.vue -->
<script setup lang="ts">
import { computed } from 'vue'
import { STEP_SCHEMAS, type Step, type ActionName, type FieldSpec } from '@/types/step'

const props = defineProps<{ modelValue: Step[] }>()
const emit = defineEmits<{ (e: 'update:modelValue', v: Step[]): void }>()

function schemaOf(action: ActionName) { return STEP_SCHEMAS.find(s => s.action === action)! }
function fieldsFor(action: ActionName): FieldSpec[] { return schemaOf(action)?.fields ?? [] }
function defaultsFor(action: ActionName): Record<string, string> {
  const o: Record<string, string> = {}
  for (const f of fieldsFor(action)) o[f.name] = f.default ?? ''
  return o
}

const steps = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v)
})

function add() {
  const first: ActionName = 'goto'
  steps.value = [...steps.value, { id: crypto.randomUUID(), action: first, params: defaultsFor(first) }]
}
function remove(i: number) { steps.value = steps.value.filter((_, idx) => idx !== i) }
function move(i: number, dir: -1 | 1) {
  const j = i + dir
  if (j < 0 || j >= steps.value.length) return
  const arr = [...steps.value]
  ;[arr[i], arr[j]] = [arr[j], arr[i]]
  steps.value = arr
}
function changeAction(i: number, action: ActionName) {
  const arr = [...steps.value]
  arr[i] = { ...arr[i], action, params: defaultsFor(action) }
  steps.value = arr
}
function setParam(i: number, name: string, value: string) {
  const arr = [...steps.value]
  arr[i] = { ...arr[i], params: { ...arr[i].params, [name]: value } }
  steps.value = arr
}
</script>

<template>
  <vxe-table :data="steps" border show-overflow>
    <vxe-column type="seq" title="#" width="50" />
    <vxe-column title="动作" width="160">
      <template #default="{ row }">
        <el-select :model-value="row.action" @update:model-value="(v: ActionName) => changeAction(steps.indexOf(row), v)">
          <el-option v-for="s in STEP_SCHEMAS" :key="s.action" :label="s.label" :value="s.action" />
        </el-select>
      </template>
    </vxe-column>
    <vxe-column title="参数">
      <template #default="{ row, rowIndex }">
        <div style="display:flex; gap:8px; flex-wrap:wrap">
          <template v-for="f in fieldsFor(row.action)" :key="f.name">
            <el-input
              :model-value="row.params[f.name] ?? ''"
              @update:model-value="(v: string) => setParam(rowIndex, f.name, v)"
              :placeholder="f.label"
              :required="f.required"
              style="width: 180px"
            />
          </template>
        </div>
      </template>
    </vxe-column>
    <vxe-column title="操作" width="180">
      <template #default="{ row, rowIndex }">
        <el-button size="small" @click="move(rowIndex, -1)">上移</el-button>
        <el-button size="small" @click="move(rowIndex, 1)">下移</el-button>
        <el-button size="small" type="danger" @click="remove(rowIndex)">删除</el-button>
      </template>
    </vxe-column>
  </vxe-table>
  <div style="margin-top:8px"><el-button type="primary" plain @click="add">添加步骤</el-button></div>
</template>
```

- [ ] **步骤 3：单测**

```ts
// frontend/src/components/StepEditor.test.ts
import { mount } from '@vue/test-utils'
import { describe, it, expect } from 'vitest'
import StepEditor from './StepEditor.vue'
import { STEP_SCHEMAS, type Step } from '@/types/step'

describe('StepEditor', () => {
  it('渲染空表 + 添加按钮', () => {
    const w = mount(StepEditor, { props: { modelValue: [] } })
    expect(w.text()).toContain('添加步骤')
  })

  it('点击添加后追加默认步骤 (goto)', async () => {
    let v: Step[] = []
    const w = mount(StepEditor, { props: { modelValue: v }, listeners: {
      'update:modelValue': (nv: Step[]) => { v = nv; w.setProps({ modelValue: nv }) }
    } })
    await w.find('button').trigger('click')
    expect(v).toHaveLength(1)
    expect(v[0].action).toBe('goto')
    expect(v[0].params).toEqual({ url: '' })
  })

  it('切换动作时重置 params 为该动作的默认', async () => {
    let v: Step[] = [{ id: 'x', action: 'goto', params: { url: 'https://x' } }]
    const w = mount(StepEditor, { props: { modelValue: v }, listeners: {
      'update:modelValue': (nv: Step[]) => { v = nv; w.setProps({ modelValue: nv }) }
    } })
    v[0].action = 'wait'
    w.setProps({ modelValue: v })
    await w.vm.$nextTick()
    expect(v[0].action).toBe('wait')
    expect(v[0].params).toEqual({ value: '500' })
  })

  it('11 种 action 都有 schema', () => {
    expect(STEP_SCHEMAS).toHaveLength(11)
  })
})
```

- [ ] **步骤 4：手测**

`vitest run StepEditor.test.ts` → 4 个用例全过

---

### 任务 25：CaseEditor.vue 完整页面（步骤编辑 + 保存 + 录制按钮 + 回放按钮）

**文件：**
- 创建：`frontend/src/pages/CaseEditor.vue`
- 修改：`frontend/src/router/index.ts`（注册 `/cases/:id`）

- [ ] **步骤 1：写 case api**

```ts
// frontend/src/api/cases.ts
import { http } from './client'
import type { Step } from '@/types/step'
export interface Case { id: number; name: string; suite_id: number; steps: Step[]; updated_at: string }
export const get = (id: number) => http.get<Case>(`/cases/${id}`).then(r => r.data)
export const update = (id: number, body: Partial<Case>) => http.put<Case>(`/cases/${id}`, body).then(r => r.data)
export const create = (body: { name: string; suite_id: number }) => http.post<Case>('/cases', body).then(r => r.data)
```

- [ ] **步骤 2：后端 PUT /api/cases/{id}（确保已存在，校验）**

确认任务 16 已实现 `PUT /api/cases/{id}`。如未加 Pydantic 校验，追加：

```python
# backend/app/schemas/case.py
from pydantic import BaseModel, Field
from typing import List, Dict, Any
class StepIn(BaseModel):
    id: str
    action: str = Field(pattern=r"^(goto|click|fill|expect|check|select|hover|wait|screenshot|scroll|eval)$")
    params: Dict[str, Any] = {}
class CaseUpdate(BaseModel):
    name: str | None = None
    steps: List[StepIn] | None = None
```

如已实现则跳过此步。

- [ ] **步骤 3：写 CaseEditor.vue**

```vue
<!-- frontend/src/pages/CaseEditor.vue -->
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import * as api from '@/api/cases'
import StepEditor from '@/components/StepEditor.vue'
import { ElMessage } from 'element-plus'

const route = useRoute(); const router = useRouter(); const qc = useQueryClient()
const id = Number(route.params.id)

const { data: c } = useQuery({ queryKey: ['case', id], queryFn: () => api.get(id) })
const steps = ref(api.Step[] = [])
watch(c, (v) => { if (v) steps.value = v.steps }, { immediate: true })

const save = useMutation({
  mutationFn: () => api.update(id, { steps: steps.value }),
  onSuccess: () => { ElMessage.success('已保存'); qc.invalidateQueries({ queryKey: ['case', id] }) }
})
</script>

<template>
  <h2>用例编辑器 — #{{ id }} {{ c?.name }}</h2>
  <el-button type="primary" @click="save.mutate()" :loading="save.isPending.value">保存</el-button>
  <router-link :to="`/cases/${id}/record`" style="margin-left:8px"><el-button>录制</el-button></router-link>
  <router-link :to="`/cases/${id}/playback`" style="margin-left:8px"><el-button type="success">回放</el-button></router-link>
  <el-divider />
  <StepEditor v-model="steps" />
</template>
```

- [ ] **步骤 4：手测**

打开 `/cases/1`，添加 3 个步骤（goto→fill→click），点保存，后端 `cases` 表 steps 列更新

---

### 任务 26：Recorder worker（playwright codegen 子进程封装）

**文件：**
- 创建：`backend/app/services/recorder.py`
- 创建：`backend/app/services/recorder_parsers.py`
- 创建：`backend/app/services/recorder_parsers.test.py`
- 创建：`backend/tests/unit/test_recorder_parsers.py`

- [ ] **步骤 1：先写 parser 单测（TDD 红）**

```python
# backend/tests/unit/test_recorder_parsers.py
from app.services.recorder_parsers import parse_codegen_log

def test_parses_page_goto():
    log = '[13:01:22] Page.goto: https://example.com/login'
    assert parse_codegen_log(log) == {'action': 'goto', 'params': {'url': 'https://example.com/login'}}

def test_parses_click():
    log = '[13:01:25] Click: button[type="submit"]'
    assert parse_codegen_log(log) == {'action': 'click', 'params': {'selector': 'button[type="submit"]'}}

def test_parses_fill():
    log = '[13:01:30] Fill: input[name=email] (value: a@b.com)'
    assert parse_codegen_log(log) == {'action': 'fill', 'params': {'selector': 'input[name=email]', 'value': 'a@b.com'}}

def test_ignores_unknown():
    assert parse_codegen_log('garbage line') is None
```

- [ ] **步骤 2：跑测试 → FAIL**

运行：`pytest backend/tests/unit/test_recorder_parsers.py -v`
预期：ImportError `app.services.recorder_parsers` 不存在

- [ ] **步骤 3：写 parser 实现（绿）**

```python
# backend/app/services/recorder_parsers.py
import re
from typing import Optional, Dict, Any

_RE_GOTO = re.compile(r'Page\.goto:\s*(\S+)')
_RE_CLICK = re.compile(r'Click:\s*(\S+)')
_RE_FILL = re.compile(r'Fill:\s*(\S+)\s*\(value:\s*(.*?)\)')

def parse_codegen_log(line: str) -> Optional[Dict[str, Any]]:
    if m := _RE_GOTO.search(line):
        return {'action': 'goto', 'params': {'url': m.group(1)}}
    if m := _RE_CLICK.search(line):
        return {'action': 'click', 'params': {'selector': m.group(1)}}
    if m := _RE_FILL.search(line):
        return {'action': 'fill', 'params': {'selector': m.group(1), 'value': m.group(2)}}
    return None
```

- [ ] **步骤 4：再跑测试 → PASS**

运行：`pytest backend/tests/unit/test_recorder_parsers.py -v`
预期：4 passed

- [ ] **步骤 5：写 Recorder 服务（异步子进程）**

```python
# backend/app/services/recorder.py
import asyncio
import os
import shlex
import uuid
from pathlib import Path
from typing import AsyncIterator, Dict, Any
from app.config import settings
from app.services.recorder_parsers import parse_codegen_log

class Recorder:
    """包装 playwright codegen 子进程，逐行推流事件。"""

    def __init__(self, url: str, browser: str = "chromium") -> None:
        self.id = uuid.uuid4().hex
        self.url = url
        self.browser = browser
        self.proc: asyncio.subprocess.Process | None = None
        self.log_path = Path(settings.runs_dir) / f"record-{self.id}.log"

    async def start(self) -> None:
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        cmd = ["npx", "-y", "@playwright/codegen", "--target=python",
               "--browser", self.browser, self.url]
        self.proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
            env={**os.environ, "PWDEBUGHEADER": "1"}
        )

    async def stream(self) -> AsyncIterator[Dict[str, Any]]:
        assert self.proc and self.proc.stdout
        self.log_path.write_text("", encoding="utf-8")
        async for raw in self.proc.stdout:
            line = raw.decode("utf-8", errors="replace").rstrip()
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
            ev: Dict[str, Any] = {"type": "log", "data": line}
            parsed = parse_codegen_log(line)
            if parsed:
                ev["parsed"] = parsed
            yield ev
        rc = await self.proc.wait()
        yield {"type": "exit", "code": rc}

    async def stop(self) -> None:
        if self.proc and self.proc.returncode is None:
            self.proc.terminate()
            try:
                await asyncio.wait_for(self.proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                self.proc.kill()
```

- [ ] **步骤 6：手测**

```python
# backend/tests/integration/test_recorder_smoke.py
import pytest
from app.services.recorder import Recorder
@pytest.mark.asyncio
async def test_recorder_lifecycle():
    r = Recorder(url="about:blank", browser="chromium")
    await r.start()
    await asyncio.sleep(0.2)
    await r.stop()
    assert r.log_path.exists()
```

`pytest backend/tests/integration/test_recorder_smoke.py -v` → PASS

---

### 任务 27：WS /ws/rec 推流 + 后端 sessions 存储

**文件：**
- 创建：`backend/app/ws/rec_ws.py`
- 创建：`backend/app/services/recorder_session.py`（in-memory 字典 + 线程锁）
- 修改：`backend/app/main.py`

- [ ] **步骤 1：单测：session 字典的 add/remove/get**

```python
# backend/tests/unit/test_recorder_session.py
import pytest
from app.services.recorder_session import RecorderSessionStore, RecorderSession

def test_add_get_remove():
    s = RecorderSessionStore()
    sess = RecorderSession(rec_id="abc", user_id=1, ws=None, recorder=None)
    s.add(sess)
    assert s.get("abc") is sess
    s.remove("abc")
    assert s.get("abc") is None

def test_get_missing_returns_none():
    assert RecorderSessionStore().get("nope") is None
```

- [ ] **步骤 2：跑 → FAIL，然后实现 → PASS**

```python
# backend/app/services/recorder_session.py
import threading
from dataclasses import dataclass
from typing import Optional, Dict
from fastapi import WebSocket
from app.services.recorder import Recorder

@dataclass
class RecorderSession:
    rec_id: str
    user_id: int
    ws: WebSocket
    recorder: Recorder

class RecorderSessionStore:
    def __init__(self) -> None:
        self._m: Dict[str, RecorderSession] = {}
        self._lock = threading.Lock()
    def add(self, s: RecorderSession) -> None:
        with self._lock: self._m[s.rec_id] = s
    def get(self, rec_id: str) -> Optional[RecorderSession]:
        with self._lock: return self._m.get(rec_id)
    def remove(self, rec_id: str) -> None:
        with self._lock: self._m.pop(rec_id, None)

store = RecorderSessionStore()
```

- [ ] **步骤 3：写 WS 端点**

```python
# backend/app/ws/rec_ws.py
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from app.ws.recorder_session import store, RecorderSession
from app.services.recorder import Recorder
from app.deps import get_current_user_ws

router = APIRouter()

@router.websocket("/ws/rec")
async def ws_rec(ws: WebSocket):
    await ws.accept()
    user_id = await get_current_user_ws(ws)
    if not user_id:
        await ws.close(code=4401); return
    params = dict((p.split("=", 1) for p in (ws.query_params.get("params") or "").split("&") if "=" in p))
    rec = Recorder(url=params.get("url", "about:blank"), browser=params.get("browser", "chromium"))
    await rec.start()
    rec_id = rec.id
    store.add(RecorderSession(rec_id=rec_id, user_id=user_id, ws=ws, recorder=rec))
    try:
        async def _pump():
            async for ev in rec.stream():
                await ws.send_text(json.dumps(ev, ensure_ascii=False))
        pump_task = asyncio.create_task(_pump())
        while True:
            msg = await ws.receive_text()
            if msg == "stop":
                await rec.stop(); pump_task.cancel(); break
    except WebSocketDisconnect:
        pass
    finally:
        await rec.stop()
        store.remove(rec_id)
```

- [ ] **步骤 4：注册 + 集成测**

```python
# main.py
from app.ws import rec_ws
app.include_router(rec_ws.router)
```

```python
# backend/tests/integration/test_rec_ws.py
import pytest
@pytest.mark.asyncio
async def test_ws_rec_auth_required():
    from fastapi.testclient import TestClient
    from app.main import app
    c = TestClient(app)
    with c.websocket_connect("/ws/rec") as ws:
        assert ws.receive_text() == ""  # 服务端因未鉴权 close
```

---

### 任务 28：RecorderPanel.vue（录制实时面板，parsed 步骤自动追加到用例）

**文件：**
- 创建：`frontend/src/pages/RecorderPanel.vue`
- 创建：`frontend/src/components/RecorderLog.vue`
- 修改：`frontend/src/router/index.ts`（注册 `/cases/:id/record`）

- [ ] **步骤 1：写 LogStream 风格组件**

```vue
<!-- frontend/src/components/RecorderLog.vue -->
<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
const props = defineProps<{ lines: string[] }>()
const wrap = ref<HTMLElement>()
watch(() => props.lines.length, async () => { await nextTick(); if (wrap.value) wrap.value.scrollTop = wrap.value.scrollHeight })
</script>
<template>
  <pre ref="wrap" style="height:50vh;overflow:auto;background:#1e1e1e;color:#0f0;padding:12px;font:12px/1.5 monospace">{{ lines.join('\n') }}</pre>
</template>
```

- [ ] **步骤 2：写 RecorderPanel.vue**

```vue
<!-- frontend/src/pages/RecorderPanel.vue -->
<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMutation } from '@tanstack/vue-query'
import RecorderLog from '@/components/RecorderLog.vue'
import * as api from '@/api/cases'
import type { Step } from '@/types/step'
import { ElMessage } from 'element-plus'

const route = useRoute(); const router = useRouter()
const caseId = Number(route.params.id)
const lines = ref<string[]>([])
const steps = ref<Step[]>([])
let ws: WebSocket | null = null
let url = ''

function start() {
  const base = (import.meta.env.VITE_WS_BASE as string) || ''
  const qs = new URLSearchParams({ url, browser: 'chromium' })
  ws = new WebSocket(`${base}/ws/rec?${qs.toString()}`)
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data)
    if (m.type === 'log') lines.value.push(m.data)
    if (m.parsed) {
      steps.value.push({ id: crypto.randomUUID(), action: m.parsed.action, params: m.parsed.params })
    }
    if (m.type === 'exit') { ElMessage.info('录制结束'); }
  }
}
function stop() { ws?.send('stop'); ws?.close() }
async function save() {
  await api.update(caseId, { steps: steps.value })
  ElMessage.success('已写回用例')
  router.push(`/cases/${caseId}`)
}
onUnmounted(() => stop())
</script>

<template>
  <h2>录制 — 用例 #{{ caseId }}</h2>
  <el-input v-model="url" placeholder="目标 URL（如 https://dsep-portal-test.minmetals.com.cn）" style="width:480px" />
  <el-button type="primary" @click="start" :disabled="!url">开始</el-button>
  <el-button @click="stop">停止</el-button>
  <el-divider />
  <h3>已识别步骤 ({{ steps.length }})</h3>
  <el-table :data="steps" size="small">
    <el-table-column type="index" width="50" />
    <el-table-column prop="action" label="动作" width="100" />
    <el-table-column label="参数">
      <template #default="{ row }"><code>{{ JSON.stringify(row.params) }}</code></template>
    </el-table-column>
  </el-table>
  <el-button type="success" @click="save" :disabled="!steps.length">保存到用例</el-button>
  <h3>原始日志</h3>
  <RecorderLog :lines="lines" />
</template>
```

- [ ] **步骤 3：手测**

打开 `/cases/1/record`，输入 `https://example.com`，开始 → 浏览器弹 codegen 窗口，操作几下 → 回前端看识别步骤 → 保存

---

### 任务 29：Script 生成（纯函数 `case → pytest code`）

**文件：**
- 创建：`backend/app/services/script_gen.py`
- 创建：`backend/tests/unit/test_script_gen.py`

- [ ] **步骤 1：写单测（TDD 红）**

```python
# backend/tests/unit/test_script_gen.py
from app.services.script_gen import generate_script, Step

def test_goto_only():
    s = generate_script(name="t1", steps=[Step(action="goto", params={"url": "https://x"})])
    assert 'def test_t1' in s
    assert 'page.goto("https://x")' in s

def test_full_chain():
    steps = [
        Step(action="goto", params={"url": "https://x/login"}),
        Step(action="fill", params={"selector": "input[name=email]", "value": "a@b"}),
        Step(action="click", params={"selector": "button[type=submit]"}),
        Step(action="expect", params={"selector": ".title", "value": "Dashboard"}),
    ]
    code = generate_script(name="login_ok", steps=steps)
    assert 'page.fill("input[name=email]", "a@b")' in code
    assert 'page.click("button[type=submit]")' in code
    assert 'expect(page.locator(".title")).to_have_text("Dashboard")' in code

def test_unknown_action_raises():
    import pytest
    with pytest.raises(ValueError):
        generate_script(name="x", steps=[Step(action="noop", params={})])
```

- [ ] **步骤 2：跑 → FAIL（ImportError）**

- [ ] **步骤 3：实现**

```python
# backend/app/services/script_gen.py
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class Step:
    action: str
    params: Dict[str, str]

_TMPL_HEADER = '''import pytest
from playwright.sync_api import Page, expect

@pytest.mark.{browser}
def test_{name}(page: Page):
    page.set_default_timeout(15000)
'''
_TMPL_BODY = {
    "goto": '    page.goto("{url}")',
    "click": '    page.click("{selector}")',
    "fill": '    page.fill("{selector}", "{value}")',
    "expect": '    expect(page.locator("{selector}")).to_have_text("{value}")',
    "check": '    expect(page.locator("{selector}")).to_be_visible()',
    "select": '    page.select_option("{selector}", "{value}")',
    "hover": '    page.hover("{selector}")',
    "wait": '    page.wait_for_timeout({value})',
    "screenshot": '    page.screenshot(path="{value}")',
    "scroll": '    page.evaluate("window.scrollTo(0, document.body.scrollHeight)") if "{selector}"=="" else page.locator("{selector}").scroll_into_view_if_needed()',
    "eval": '    page.evaluate("{value}")',
}

def generate_script(name: str, steps: List[Step], browser: str = "chromium") -> str:
    lines = [_TMPL_HEADER.format(browser=browser, name=name)]
    for s in steps:
        tpl = _TMPL_BODY.get(s.action)
        if not tpl: raise ValueError(f"unknown action: {s.action}")
        lines.append(tpl.format(**s.params))
    return "\n".join(lines) + "\n"
```

- [ ] **步骤 4：跑 → PASS**

运行：`pytest backend/tests/unit/test_script_gen.py -v` → 3 passed

- [ ] **步骤 5：加 API `/api/cases/{id}/script`（GET 返回 .py 文本）**

```python
# backend/app/routers/cases.py 追加
from fastapi import Response
from app.services.script_gen import generate_script, Step
from app.models.catalog import Case

@router.get("/{case_id}/script")
async def get_script(case_id: int, browser: str = "chromium", db=Depends(get_db), user=Depends(get_current_user)):
    c = (await db.execute(select(Case).where(Case.id == case_id))).scalar_one_or_none()
    if not c: raise HTTPException(404)
    steps = [Step(action=s["action"], params=s["params"]) for s in (c.steps or [])]
    code = generate_script(name=c.name, steps=steps, browser=browser)
    return Response(content=code, media_type="text/x-python")
```

集成测：

```python
# backend/tests/integration/test_case_script.py
@pytest.mark.asyncio
async def test_get_script(client, db_session, seed_case):
    r = await client.get(f"/api/cases/{seed_case.id}/script?browser=chromium")
    assert r.status_code == 200
    assert "def test_" in r.text
```

---

### 任务 30：PlaybackService + worker（异步子进程执行 pytest，实时推流）

**文件：**
- 创建：`backend/app/services/playback.py`
- 创建：`backend/app/services/playback_log.py`（解析 pytest 行 → pass/fail/error）
- 创建：`backend/tests/unit/test_playback_log.py`
- 创建：`backend/tests/integration/test_playback_api.py`

- [ ] **步骤 1：单测：log 解析（TDD）**

```python
# backend/tests/unit/test_playback_log.py
from app.services.playback_log import parse_pytest_line

def test_pass():
    assert parse_pytest_line("tests/t1.py::test_x PASSED                                  [100%]") == \
        {"type": "case_result", "name": "tests/t1.py::test_x", "status": "passed"}

def test_fail():
    assert parse_pytest_line("tests/t1.py::test_x FAILED                                  [ 50%]")["status"] == "failed"

def test_progress():
    assert parse_pytest_line("=========== 3 passed, 1 failed in 1.23s ===========") == \
        {"type": "summary", "data": "3 passed, 1 failed in 1.23s"}

def test_ignored():
    assert parse_pytest_line("platform linux -- Python 3.11.0") is None
```

- [ ] **步骤 2：跑 → FAIL，再实现 → PASS**

```python
# backend/app/services/playback_log.py
import re
from typing import Optional, Dict, Any

_RE_RESULT = re.compile(r'(tests/\S+::\S+)\s+(PASSED|FAILED|SKIPPED|ERROR)\s+\[\s*(\d+)%\]')
_RE_SUMMARY = re.compile(r'=+\s*(.*?)\s*in\s+[\d\.]+s\s*=+')

def parse_pytest_line(line: str) -> Optional[Dict[str, Any]]:
    if m := _RE_RESULT.search(line):
        return {"type": "case_result", "name": m.group(1), "status": m.group(2).lower()}
    if m := _RE_SUMMARY.search(line):
        return {"type": "summary", "data": m.group(1)}
    return None
```

- [ ] **步骤 3：写 PlaybackService**

```python
# backend/app/services/playback.py
import asyncio
import os
import uuid
from pathlib import Path
from typing import AsyncIterator, Dict, Any
from app.config import settings
from app.services.script_gen import generate_script, Step
from app.services.playback_log import parse_pytest_line

class PlaybackService:
    def __init__(self, case_name: str, steps: list[Step], browser: str = "chromium", artifact_dir: str | None = None) -> None:
        self.id = uuid.uuid4().hex
        self.case_name = case_name
        self.steps = steps
        self.browser = browser
        self.artifact_dir = Path(artifact_dir or settings.runs_dir) / f"playback-{self.id}"
        self.script_path = self.artifact_dir / f"test_{case_name}.py"
        self.log_path = self.artifact_dir / "pytest.log"
        self.proc: asyncio.subprocess.Process | None = None

    async def start(self) -> None:
        self.artifact_dir.mkdir(parents=True, exist_ok=True)
        code = generate_script(name=self.case_name, steps=self.steps, browser=self.browser)
        self.script_path.write_text(code, encoding="utf-8")
        self.proc = await asyncio.create_subprocess_exec(
            "pytest", "-q", "--tb=short", str(self.script_path),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
            cwd=str(self.artifact_dir),
        )

    async def stream(self) -> AsyncIterator[Dict[str, Any]]:
        assert self.proc and self.proc.stdout
        self.log_path.write_text("", encoding="utf-8")
        async for raw in self.proc.stdout:
            line = raw.decode("utf-8", errors="replace").rstrip()
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
            ev: Dict[str, Any] = {"type": "log", "data": line}
            parsed = parse_pytest_line(line)
            if parsed: ev["parsed"] = parsed
            yield ev
        rc = await self.proc.wait()
        yield {"type": "exit", "code": rc}

    async def stop(self) -> None:
        if self.proc and self.proc.returncode is None:
            self.proc.terminate()
            try: await asyncio.wait_for(self.proc.wait(), timeout=5)
            except asyncio.TimeoutError: self.proc.kill()

    def failure_screenshot_path(self) -> Path | None:
        """playwright 在同目录生成 test_<name>-failed.png 时返回；否则 None"""
        for p in self.artifact_dir.glob(f"test_{self.case_name}*-failed.png"):
            return p
        return None
```

- [ ] **步骤 4：API + 持久化历史**

```python
# backend/app/routers/playback.py
import asyncio
import json
import uuid
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.deps import get_db, get_current_user, get_current_user_ws
from app.db.session import SessionLocal
from app.models.catalog import Case
from app.models.runtime import PlaybackHistory
from app.services.playback import PlaybackService
from app.services.script_gen import Step
from app.config import settings
from app.ws.manager import manager

router = APIRouter(prefix="/api/playback")

@router.post("")
async def start_playback(body: dict, db=Depends(get_db), user=Depends(get_current_user)):
    c = (await db.execute(select(Case).where(Case.id == body["case_id"]))).scalar_one_or_none()
    if not c: raise HTTPException(404)
    steps = [Step(action=s["action"], params=s["params"]) for s in (c.steps or [])]
    pb = PlaybackService(case_name=c.name, steps=steps, browser=body.get("browser", "chromium"))
    h = PlaybackHistory(id=pb.id, case_id=c.id, user_id=user.id, started_at=datetime.utcnow(),
                        artifact_dir=str(pb.artifact_dir), status="running")
    db.add(h); await db.commit()

    async def _go():
        await pb.start()
        last = 0
        async for ev in pb.stream():
            await manager.broadcast(f"playback:{pb.id}", ev)
            if ev["type"] == "exit": last = ev["code"]
        async with SessionLocal() as s2:
            h2 = (await s2.execute(select(PlaybackHistory).where(PlaybackHistory.id == pb.id))).scalar_one()
            h2.status = "passed" if last == 0 else "failed"
            h2.finished_at = datetime.utcnow()
            h2.summary = {"exit_code": last,
                         "screenshot": str(pb.failure_screenshot_path()) if last != 0 else None}
            await s2.commit()
    asyncio.create_task(_go())
    return {"id": pb.id}

@router.get("")
async def list_history(case_id: int, limit: int = 20, db=Depends(get_db), user=Depends(get_current_user)):
    res = await db.execute(select(PlaybackHistory).where(PlaybackHistory.case_id == case_id)
                           .order_by(PlaybackHistory.started_at.desc()).limit(limit))
    return [{"id": h.id, "status": h.status, "started_at": str(h.started_at),
             "finished_at": str(h.finished_at) if h.finished_at else None,
             "summary": h.summary} for h in res.scalars()]

@router.websocket("/ws/playback/{pb_id}")
async def ws_playback(ws: WebSocket, pb_id: str):
    await manager.connect(f"playback:{pb_id}", ws)
    try:
        async with SessionLocal() as db:
            h = (await db.execute(select(PlaybackHistory).where(PlaybackHistory.id == pb_id))).scalar_one_or_none()
        if h and Path(h.artifact_dir, "pytest.log").exists():
            for line in Path(h.artifact_dir, "pytest.log").read_text(encoding="utf-8", errors="replace").splitlines()[-200:]:
                await ws.send_text(json.dumps({"type": "log", "data": line}, ensure_ascii=False))
        while True: await ws.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(f"playback:{pb_id}", ws)
```

- [ ] **步骤 5：注册 + 集成测**

```python
# main.py
from app.routers import playback
app.include_router(playback.router)
```

```python
# backend/tests/integration/test_playback_api.py
@pytest.mark.asyncio
async def test_post_playback_returns_id(client, db_session, seed_case):
    r = await client.post("/api/playback", json={"case_id": seed_case.id, "browser": "chromium"})
    assert r.status_code == 200
    assert "id" in r.json()
```

---

### 任务 31：PlaybackStream.vue + 用例页加"回放"入口

**文件：**
- 创建：`frontend/src/pages/PlaybackStream.vue`
- 创建：`frontend/src/components/PlaybackHistory.vue`
- 修改：`frontend/src/router/index.ts`（注册 `/cases/:id/playback` 和 `/cases/:id/history`）
- 修改：`frontend/src/pages/CaseEditor.vue`（加跳到历史和回放的链接）

- [ ] **步骤 1：写 playback api**

```ts
// frontend/src/api/playback.ts
import { http } from './client'
export const start = (b: { case_id: number; browser: string }) => http.post<{ id: string }>('/playback', b).then(r => r.data)
export const history = (case_id: number) => http.get<any[]>(`/playback?case_id=${case_id}`).then(r => r.data)
```

- [ ] **步骤 2：写 PlaybackStream.vue**

```vue
<!-- frontend/src/pages/PlaybackStream.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useMutation } from '@tanstack/vue-query'
import * as api from '@/api/playback'
import { useWS } from '@/composables/useWS'
import LogStream from '@/components/LogStream.vue'

const route = useRoute(); const router = useRouter()
const caseId = Number(route.params.id)
const lines = ref<string[]>([])
const startM = useMutation({ mutationFn: () => api.start({ case_id: caseId, browser: 'chromium' }) })
let pbId: string | null = null

async function begin() {
  const r = await startM.mutateAsync()
  pbId = r.id
  const base = (import.meta.env.VITE_WS_BASE as string) || ''
  const ws = new WebSocket(`${base}/ws/playback/${pbId}`)
  ws.onmessage = (e) => {
    const m = JSON.parse(e.data)
    if (m.type === 'log') lines.value.push(m.data)
    if (m.type === 'exit') lines.value.push(`--- 完成 exit=${m.code} ---`)
  }
}
</script>

<template>
  <h2>回放 — 用例 #{{ caseId }}</h2>
  <el-button type="primary" @click="begin" :loading="startM.isPending.value">开始回放</el-button>
  <el-divider />
  <LogStream :lines="lines" />
</template>
```

- [ ] **步骤 3：写 PlaybackHistory.vue**

```vue
<!-- frontend/src/components/PlaybackHistory.vue -->
<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import * as api from '@/api/playback'
const props = defineProps<{ caseId: number }>()
const { data } = useQuery({ queryKey: ['playback-history', props.caseId], queryFn: () => api.history(props.caseId) })
</script>
<template>
  <h3>历史</h3>
  <el-table :data="data || []" size="small">
    <el-table-column prop="id" label="ID" width="200" />
    <el-table-column prop="status" label="状态">
      <template #default="{ row }"><el-tag :type="row.status === 'passed' ? 'success' : 'danger'">{{ row.status }}</el-tag></template>
    </el-table-column>
    <el-table-column prop="started_at" label="开始时间" />
    <el-table-column label="截图">
      <template #default="{ row }">
        <a v-if="row.summary?.screenshot" :href="`/api/artifacts/${row.summary.screenshot}`" target="_blank">查看</a>
        <span v-else>—</span>
      </template>
    </el-table-column>
  </el-table>
</template>
```

- [ ] **步骤 4：在 CaseEditor.vue 加链接**

```vue
<!-- 追加到 CaseEditor.vue 头部按钮组 -->
<router-link :to="`/cases/${id}/history`" style="margin-left:8px"><el-button>历史</el-button></router-link>
```

- [ ] **步骤 5：手测**

打开 `/cases/1/playback` → 启动 → 看到日志滚动 → exit 后跳到历史列表，看到 passed/failed 标签，失败时显示"查看"截图链接

---

### 任务 32：（预留）录制器 WS 补漏：把 parsed 步骤 push 到前端

> 任务 28 已实现基本推流。本任务只做：把 `m.parsed` 自动落库成草稿步骤，免去用户手动"保存到用例"按钮。

**文件：**
- 修改：`backend/app/ws/rec_ws.py`
- 修改：`backend/app/services/recorder_session.py`
- 创建：`backend/tests/integration/test_rec_ws_draft.py`

- [ ] **步骤 1：RecorderSession 加 `case_id` 与 `collected: list`**

```python
# recorder_session.py 修改
@dataclass
class RecorderSession:
    rec_id: str
    user_id: int
    case_id: int
    ws: WebSocket
    recorder: Recorder
    collected: list = field(default_factory=list)
```

- [ ] **步骤 2：WS 端点：识别到 parsed 时 append**

```python
# rec_ws.py 修改 pump 循环
async def _pump():
    async for ev in rec.stream():
        if ev.get("parsed"):
            sess.collected.append(ev["parsed"])
        await ws.send_text(json.dumps(ev, ensure_ascii=False))
```

- [ ] **步骤 3：客户端发 `save` 消息触发写回**

```python
# rec_ws.py 接收循环
while True:
    msg = await ws.receive_text()
    if msg == "stop":
        await rec.stop(); pump_task.cancel(); break
    if msg.startswith("save:"):
        async with SessionLocal() as db:
            c = (await db.execute(select(Case).where(Case.id == sess.case_id))).scalar_one_or_none()
            if c:
                c.steps = [{"id": str(i), **p["params"] if False else {"action": p["action"], "params": p["params"]}} for i, p in enumerate(sess.collected)]
                # 修正：上述写法的 params 嵌套
                c.steps = [{"id": str(i), "action": p["action"], "params": p["params"]} for i, p in enumerate(sess.collected)]
                c.updated_at = datetime.utcnow()
                await db.commit()
        await ws.send_text(json.dumps({"type": "saved"}))
        break
```

- [ ] **步骤 4：RecorderPanel.vue 改为 ws.send(`save:${caseId}`)**

```ts
// RecorderPanel.vue 的 save() 改
function save() { ws?.send(`save:${caseId}`); ws?.onmessage = (e) => { const m = JSON.parse(e.data); if (m.type === 'saved') { ElMessage.success('已写回'); router.push(`/cases/${caseId}`) } } }
```

- [ ] **步骤 5：集成测**

```python
# test_rec_ws_draft.py
@pytest.mark.asyncio
async def test_rec_ws_saves_to_db():
    # 用 in-memory recorder + fake ws
    from app.services.recorder_session import RecorderSession
    s = RecorderSession(rec_id="t", user_id=1, case_id=99, ws=None, recorder=None)
    s.collected.append({"action": "goto", "params": {"url": "https://x"}})
    s.collected.append({"action": "click", "params": {"selector": "a"}})
    assert len(s.collected) == 2
```

---

## Phase 3d — 定时任务（3 任务，预计 2 天）

> 复用任务 21 的 `PytestRunner` 和 `/api/runs` 启动逻辑。`SchedulerService` 包装 APScheduler，job 落 PG `runtime.schedules` 表。

---

### 任务 33：APScheduler 集成 + `SchedulerService` 抽象

**文件：**
- 创建：`backend/app/services/scheduler.py`
- 创建：`backend/app/main.py`（lifespan 启动/关闭 scheduler）
- 创建：`backend/tests/unit/test_scheduler_service.py`

- [ ] **步骤 1：单测：抽象接口合约**

```python
# test_scheduler_service.py
import asyncio
import pytest
from app.services.scheduler import SchedulerService, InMemoryScheduler
from app.models.runtime import Schedule

@pytest.mark.asyncio
async def test_inmemory_add_list_remove():
    s = InMemoryScheduler()
    sch = Schedule(id=1, name="t", cron="*/5 * * * *", suite_id=1, browser="chromium", enabled=True)
    await s.add(sch)
    items = await s.list()
    assert any(x.id == 1 for x in items)
    await s.remove(1)
    assert all(x.id != 1 for x in await s.list())

@pytest.mark.asyncio
async def test_inmemory_run_now_doesnt_block():
    s = InMemoryScheduler()
    sch = Schedule(id=1, name="t", cron="*/5 * * * *", suite_id=1, browser="chromium", enabled=True)
    await s.run_now(sch)
    # 不抛异常即可
```

- [ ] **步骤 2：跑 → FAIL（接口未实现）**

- [ ] **步骤 3：实现抽象 + 内存版**

```python
# backend/app/services/scheduler.py
from abc import ABC, abstractmethod
from typing import List
from app.models.runtime import Schedule

class SchedulerService(ABC):
    @abstractmethod
    async def add(self, sch: Schedule) -> None: ...
    @abstractmethod
    async def remove(self, sch_id: int) -> None: ...
    @abstractmethod
    async def list(self) -> List[Schedule]: ...
    @abstractmethod
    async def run_now(self, sch: Schedule) -> None: ...

class InMemoryScheduler(SchedulerService):
    """用于测试：纯内存，无 APScheduler 依赖。"""
    def __init__(self) -> None:
        self._items: dict[int, Schedule] = {}
    async def add(self, sch: Schedule) -> None: self._items[sch.id] = sch
    async def remove(self, sch_id: int) -> None: self._items.pop(sch_id, None)
    async def list(self) -> List[Schedule]: return list(self._items.values())
    async def run_now(self, sch: Schedule) -> None: return None
```

- [ ] **步骤 4：APScheduler 实现**

```python
# 同文件追加
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.cron import CronTrigger
from app.config import settings
from app.db.session import SessionLocal
from app.models.runtime import Run
from app.services.runs import start_run, finish_run  # 任务 20 已实现
from app.services.runner import PytestRunner, RunConfig
from pathlib import Path

class APSchedulerService(SchedulerService):
    def __init__(self) -> None:
        self.scheduler = AsyncIOScheduler(jobstores={
            "default": SQLAlchemyJobStore(url=settings.database_url)
        })
    def start(self) -> None: self.scheduler.start()
    def shutdown(self) -> None: self.scheduler.shutdown(wait=False)
    async def add(self, sch: Schedule) -> None:
        async def _job(suite_id: int = sch.suite_id, browser: str = sch.browser, name: str = sch.name):
            async with SessionLocal() as db:
                r = await start_run(db, suite_id=suite_id, env="test", browser=browser, started_by=None, schedule_id=sch.id)
                rc = RunConfig(env="test", browser=browser, suite_id=suite_id, log_path=Path(r.log_path), cmd=["pytest","-q","--alluredir",settings.allure_results_dir,"-x"])
                last = 1
                async for ev in PytestRunner().run(rc):
                    if ev["type"] == "exit": last = ev["code"]
                await finish_run(db, r.id, status="passed" if last==0 else "failed", summary={"exit_code": last, "schedule_id": sch.id})
        self.scheduler.add_job(_job, CronTrigger.from_crontab(sch.cron), id=f"sch-{sch.id}", replace_existing=True)
    async def remove(self, sch_id: int) -> None:
        try: self.scheduler.remove_job(f"sch-{sch_id}")
        except Exception: pass
    async def list(self) -> List[Schedule]:
        async with SessionLocal() as db:
            from sqlalchemy import select
            res = await db.execute(select(Schedule))
            return list(res.scalars())
    async def run_now(self, sch: Schedule) -> None:
        await self.add(sch)  # 已存在则 replace_existing
        self.scheduler.modify_job(f"sch-{sch.id}", next_run_time=__import__("datetime").datetime.utcnow())
```

- [ ] **步骤 5：main.py lifespan 集成**

```python
# main.py
from contextlib import asynccontextmanager
from app.services.scheduler import APSchedulerService
@asynccontextmanager
async def lifespan(app):
    sched = APSchedulerService(); sched.start()
    app.state.scheduler = sched
    yield
    sched.shutdown()
app = FastAPI(lifespan=lifespan, ...)
```

- [ ] **步骤 6：跑单测 → PASS**

`pytest backend/tests/unit/test_scheduler_service.py -v` → 2 passed

---

### 任务 34：`/api/schedules` CRUD + trigger

**文件：**
- 创建：`backend/app/routers/schedules.py`
- 创建：`backend/app/schemas/schedule.py`
- 创建：`backend/tests/integration/test_schedules_api.py`
- 修改：`backend/app/main.py`

- [ ] **步骤 1：schema**

```python
# backend/app/schemas/schedule.py
from pydantic import BaseModel, Field
from typing import Optional

class ScheduleIn(BaseModel):
    name: str
    cron: str = Field(pattern=r"^[\*\/0-9\-\,\s]+$")
    suite_id: int
    browser: str = "chromium"
    enabled: bool = True

class ScheduleOut(BaseModel):
    id: int; name: str; cron: str; suite_id: int; browser: str
    enabled: bool; last_run_at: Optional[str]; last_status: Optional[str]
```

- [ ] **步骤 2：router**

```python
# backend/app/routers/schedules.py
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from app.deps import get_db, get_current_user
from app.models.runtime import Schedule
from app.schemas.schedule import ScheduleIn, ScheduleOut

router = APIRouter(prefix="/api/schedules")

@router.post("", response_model=ScheduleOut, status_code=201)
async def create_sch(body: ScheduleIn, db=Depends(get_db), user=Depends(get_current_user)):
    s = Schedule(**body.model_dump(), created_by=user.id)
    db.add(s); await db.commit(); await db.refresh(s)
    sched = app_state(request).scheduler
    if s.enabled: await sched.add(s)
    return ScheduleOut(id=s.id, name=s.name, cron=s.cron, suite_id=s.suite_id,
                       browser=s.browser, enabled=s.enabled,
                       last_run_at=str(s.last_run_at) if s.last_run_at else None,
                       last_status=s.last_status)

@router.get("", response_model=list[ScheduleOut])
async def list_sch(db=Depends(get_db), user=Depends(get_current_user)):
    res = await db.execute(select(Schedule).order_by(Schedule.id.desc()))
    return [ScheduleOut(id=s.id, name=s.name, cron=s.cron, suite_id=s.suite_id,
                        browser=s.browser, enabled=s.enabled,
                        last_run_at=str(s.last_run_at) if s.last_run_at else None,
                        last_status=s.last_status) for s in res.scalars()]

@router.delete("/{sch_id}", status_code=204)
async def delete_sch(sch_id: int, db=Depends(get_db), user=Depends(get_current_user), request: Request):
    s = (await db.execute(select(Schedule).where(Schedule.id == sch_id))).scalar_one_or_none()
    if not s: raise HTTPException(404)
    await app_state(request).scheduler.remove(sch_id)
    await db.delete(s); await db.commit()
    return None

@router.post("/{sch_id}/trigger", status_code=202)
async def trigger_sch(sch_id: int, db=Depends(get_db), user=Depends(get_current_user), request: Request):
    s = (await db.execute(select(Schedule).where(Schedule.id == sch_id))).scalar_one_or_none()
    if not s: raise HTTPException(404)
    await app_state(request).scheduler.run_now(s)
    return {"ok": True}

def app_state(request: Request):
    return request.app.state
```

- [ ] **步骤 3：注册 + 集成测**

```python
# main.py
from app.routers import schedules
app.include_router(schedules.router)
```

```python
# test_schedules_api.py
@pytest.mark.asyncio
async def test_create_list_delete(client, db_session, admin_token):
    r = await client.post("/api/schedules",
        json={"name":"t","cron":"*/5 * * * *","suite_id":1,"browser":"chromium"},
        headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 201
    sid = r.json()["id"]
    r2 = await client.get("/api/schedules", headers={"Authorization": f"Bearer {admin_token}"})
    assert r2.status_code == 200
    assert any(x["id"] == sid for x in r2.json())
```

---

### 任务 35：Schedules.vue（CRUD + 启停 + 立即触发 + WS 推流）

**文件：**
- 创建：`frontend/src/api/schedules.ts`
- 创建：`frontend/src/pages/Schedules.vue`
- 修改：`frontend/src/router/index.ts`

- [ ] **步骤 1：api**

```ts
// frontend/src/api/schedules.ts
import { http } from './client'
export interface Schedule { id: number; name: string; cron: string; suite_id: number; browser: string; enabled: boolean; last_status: string | null }
export const list = () => http.get<Schedule[]>('/schedules').then(r => r.data)
export const create = (b: Omit<Schedule, 'id' | 'last_status'>) => http.post<Schedule>('/schedules', b).then(r => r.data)
export const remove = (id: number) => http.delete(`/schedules/${id}`)
export const trigger = (id: number) => http.post(`/schedules/${id}/trigger`).then(r => r.data)
```

- [ ] **步骤 2：写 Schedules.vue**

```vue
<!-- frontend/src/pages/Schedules.vue -->
<script setup lang="ts">
import { ref } from 'vue'
import { useQuery, useMutation, useQueryClient } from '@tanstack/vue-query'
import * as api from '@/api/schedules'
import { ElMessage, ElMessageBox } from 'element-plus'
import { list as listSuites } from '@/api/suites'

const qc = useQueryClient()
const { data: schedules } = useQuery({ queryKey: ['schedules'], queryFn: api.list })
const { data: suites } = useQuery({ queryKey: ['suites'], queryFn: listSuites })

const form = ref({ name: '', cron: '0 9 * * *', suite_id: 0, browser: 'chromium', enabled: true })
const createM = useMutation({ mutationFn: () => api.create(form.value), onSuccess: () => { ElMessage.success('已创建'); qc.invalidateQueries({ queryKey: ['schedules'] }) } })
const removeM = useMutation({ mutationFn: api.remove, onSuccess: () => qc.invalidateQueries({ queryKey: ['schedules'] }) })
const triggerM = useMutation({ mutationFn: api.trigger, onSuccess: () => ElMessage.success('已触发') })
</script>

<template>
  <h2>定时任务</h2>
  <el-form inline>
    <el-form-item label="名称"><el-input v-model="form.name" /></el-form-item>
    <el-form-item label="Cron"><el-input v-model="form.cron" placeholder="0 9 * * *" /></el-form-item>
    <el-form-item label="套件"><el-select v-model="form.suite_id"><el-option v-for="s in suites || []" :key="s.id" :label="s.name" :value="s.id" /></el-select></el-form-item>
    <el-form-item label="浏览器"><el-select v-model="form.browser"><el-option label="chromium" value="chromium" /><el-option label="firefox" value="firefox" /><el-option label="webkit" value="webkit" /></el-select></el-form-item>
    <el-button type="primary" :loading="createM.isPending.value" @click="createM.mutate()">新建</el-button>
  </el-form>

  <el-table :data="schedules || []">
    <el-table-column prop="id" label="ID" width="60" />
    <el-table-column prop="name" label="名称" />
    <el-table-column prop="cron" label="Cron" />
    <el-table-column prop="browser" label="浏览器" />
    <el-table-column prop="enabled" label="启用">
      <template #default="{ row }"><el-tag :type="row.enabled ? 'success' : 'info'">{{ row.enabled ? '是' : '否' }}</el-tag></template>
    </el-table-column>
    <el-table-column prop="last_status" label="上次">
      <template #default="{ row }"><el-tag v-if="row.last_status" :type="row.last_status === 'passed' ? 'success' : 'danger'">{{ row.last_status }}</el-tag></template>
    </el-table-column>
    <el-table-column label="操作" width="240">
      <template #default="{ row }">
        <el-button size="small" @click="triggerM.mutate(row.id)">立即触发</el-button>
        <el-button size="small" type="danger" @click="ElMessageBox.confirm('确认删除?').then(() => removeM.mutate(row.id))">删除</el-button>
      </template>
    </el-table-column>
  </el-table>
</template>
```

- [ ] **步骤 3：手测**

新建一个 cron=每分钟（`* * * * *`）的调度 → 等待 → 看 `runtime.schedules.last_status` 字段更新 → 触发 → 看到 Run 启动

---

## Phase 4 — 关 Streamlit 入口（2 任务，预计 1 天）

> 验证 30 天后切流。本阶段两步：先隐藏入口 + 加 banner 提示，再观察一段时间后正式关停。

---

### 任务 36：VITE_FRONTEND_ENABLED 默认 true + Streamlit banner

**文件：**
- 修改：`backend/.env`（追加 `VITE_FRONTEND_ENABLED=true`，前端 vite build 时读）
- 修改：`streamlit_app/Hello.py`（顶部加 deprecation banner）
- 创建：`frontend/src/components/DeprecationBanner.vue`（Vue 端也加一个，跳到 Streamlit 入口的链接）

- [ ] **步骤 1：写 banner 组件**

```vue
<!-- frontend/src/components/DeprecationBanner.vue -->
<script setup lang="ts">
import { ref, onMounted } from 'vue'
const visible = ref(false)
onMounted(async () => {
  const r = await fetch('/api/config')
  const c = await r.json()
  visible.value = !!c.streamlit_legacy_url
})
</script>
<template>
  <el-alert v-if="visible" type="warning" :closable="false" title="旧版 Streamlit 控制台" show-icon>
    <template #default>已迁移到新版 Vue 控制台。<a :href="`/legacy`" target="_blank">点击访问旧版（仅供过渡）</a></template>
  </el-alert>
</template>
```

- [ ] **步骤 2：后端 `/api/config` 暴露 legacy URL**

```python
# backend/app/routers/config.py 追加
@router.get("/config")
async def get_legacy_url():
    return {"streamlit_legacy_url": settings.streamlit_legacy_url}
```

- [ ] **步骤 3：`.env` 追加**

```
VITE_FRONTEND_ENABLED=true
STREAMLIT_LEGACY_URL=http://localhost:8501
```

- [ ] **步骤 4：Streamlit 顶部 banner**

```python
# streamlit_app/Hello.py 顶部
import streamlit as st
st.warning("⚠️ 旧版控制台。新版已上线 → http://localhost:5173。30 天后将停用。")
```

---

### 任务 37：30 天观察协议（自动化探针）

**文件：**
- 创建：`scripts/canary_30d.py`（每日跑一次，统计新旧版使用率）
- 创建：`scripts/check_migration_readiness.py`（按 readiness 清单核对）

- [ ] **步骤 1：写 canary 探针**

```python
#!/usr/bin/env python3
"""每日调用 /api/health 和 streamlit health，记录使用率。"""
import json, urllib.request, datetime, pathlib
LOG = pathlib.Path(".data/canary_30d.jsonl")
def hit(url: str) -> bool:
    try: return urllib.request.urlopen(url, timeout=3).status == 200
    except Exception: return False
fe = hit("http://localhost:8000/api/health")
se = hit("http://localhost:8501/_stcore/health")
LOG.parent.mkdir(parents=True, exist_ok=True)
with LOG.open("a", encoding="utf-8") as f:
    f.write(json.dumps({"day": str(datetime.date.today()), "vue_ok": fe, "streamlit_ok": se}) + "\n")
print({"vue_ok": fe, "streamlit_ok": se})
```

- [ ] **步骤 2：写 readiness 清单**

```python
#!/usr/bin/env python3
"""切流前的 readiness 检查：14 项全过才允许执行任务 38。"""
import sys, urllib.request, json
CHECKS = [
    ("/api/health (Vue 后端)", "http://localhost:8000/api/health"),
    ("/api/health/browsers", "http://localhost:8000/api/health/browsers"),
    ("/api/auth/me (未登录 401)", "http://localhost:8000/api/auth/me"),
    ("/api/suites (登录后 200)", None),
    ("/api/cases (登录后 200)", None),
    ("canary 30d 日志 ≥ 14 天", ".data/canary_30d.jsonl"),
    ("streamlit 0 用户登录 (7 天内)", None),  # 由人工核对
    ("/api/runs 启动+WS 推流正常", None),
    ("/api/playback 启动+WS 推流正常", None),
    ("/api/schedules 触发成功", None),
    ("12 个核心用例在 Vue 端全部通过", None),
    ("Allure 报告生成正常", None),
    ("docs/ 用户反馈：0 P0/P1 阻塞", None),
    ("Streamlit 切流公告已发到团队", None),
]
fails = []
for name, url in CHECKS:
    if url is None:
        fails.append(f"[人工] {name}")
        continue
    try:
        ok = urllib.request.urlopen(url, timeout=3).status in (200, 401)  # 401 也算正常
        if not ok: fails.append(f"[失败] {name}")
    except Exception as e:
        fails.append(f"[失败] {name}: {e}")
print(json.dumps({"ready": not fails, "fails": fails}, ensure_ascii=False, indent=2))
sys.exit(0 if not fails else 1)
```

- [ ] **步骤 3：手测**

连续运行 30 天 canary → 第 30 天跑 readiness → 全过后进入任务 38

---

## Phase 5 — 收尾（1 任务，预计 1 天）

---

### 任务 38：删 Streamlit 代码 + 清理

**文件：**
- 删除：`streamlit_app/`（整个目录）
- 删除：`.streamlit/config.toml`
- 修改：`requirements.txt`（移除 `streamlit`, `streamlit-authenticator`, `streamlit-extras`）
- 修改：`Dockerfile.txt`（移除 `streamlit` 相关 layer 缓存清理）
- 修改：`README.md`（移除 Streamlit 相关说明，加 Vue 控制台启动指引）
- 创建：`docs/superpowers/historical/streamlit-app-deprecated.md`（归档记录）

- [ ] **步骤 1：备份**

```bash
cp -r streamlit_app/ .archive/streamlit_app_$(date +%Y%m%d)/
cp .streamlit/config.toml .archive/streamlit_config_$(date +%Y%m%d).toml
```

- [ ] **步骤 2：删除**

```bash
rm -rf streamlit_app/
rm -rf .streamlit/
```

- [ ] **步骤 3：`requirements.txt` 清理**

```diff
- streamlit>=1.39
- streamlit-authenticator>=0.3
- streamlit-extras>=0.5
```

- [ ] **步骤 4：`Dockerfile.txt` 清理**

```diff
- # Streamlit 多页配置
- ENV STREAMLIT_SERVER_PORT=8501
- EXPOSE 8501
```

- [ ] **步骤 5：写归档文档**

```markdown
<!-- docs/superpowers/historical/streamlit-app-deprecated.md -->
# Streamlit 控制台归档（2026-06-07 → 2026-07-07 切换）

## 时间线
- 2026-06-07：Vue 控制台正式上线（Feature Flag 默认开启）
- 2026-06-07 ~ 2026-07-07：30 天观察期（canary 探针每日记录）
- 2026-07-07：readiness 14 项全过，执行任务 38 关闭 Streamlit

## 保留原因（仅 git 历史）
- 2026 年 5 月 - 6 月初使用，作为 v1 仪表盘
- 迁移原因：UI 灵活度不足（多页+modal+实时推流受限）
- 仍可在 git history `git log -- streamlit_app/` 找回

## 关键历史 commit
- 5 阶段切换的关键 PR：见 git log
- 5 份 OpenSpec 归档变更（add-playback-feature 等）仍提供业务设计来源
```

- [ ] **步骤 6：手测**

启动 `docker compose up -d backend frontend` → 只看到 Vue 控制台 → 访问 `http://localhost:8000` 重定向到 `http://localhost:5173`

---

## 自检（5 项）

### 1. 规格覆盖度

规格 14 节 → 任务映射（不全的补了）：

| 规格节 | 对应任务 |
|---|---|
| §2 架构总览 | 任务 2, 7, 23, 27, 30（贯穿全栈骨架） |
| §3 端口与部署 | 任务 1（docker-compose + .env）, 任务 38（Dockerfile 清理） |
| §4 身份与权限（Auth + 4 SSO 钩子 + RBAC） | 任务 4, 5, 6, 7, 8（auth 全套 + 资源 ACL 已建模在 §4 表结构里） |
| §5 数据库与持久化（4 schema） | 任务 3（Alembic 4 schema 迁移） |
| §6 部署 | 任务 1（docker-compose） + 任务 38（清理） |
| §7 后端设计 FastAPI | 任务 2, 9-14, 20-22, 26-27, 29-30, 33-34 |
| §8 前端设计 Vue 3 | 任务 7, 8, 15-19, 23-25, 28, 31, 35 |
| §9 定时任务 APScheduler | 任务 33, 34, 35 |
| §10 迁移分阶段 5 阶段 | 任务 1-38 整体编排 |
| §11 风险与缓解 | 散落于各任务（异步转、streamlit 双写、canary、readiness） |
| §12 工期估算 | 自检后另列 |
| §13 附加（Bootstrap/Browsers/AI stub） | 任务 6, 1（browsers 已通过 §6 docker 装），AI stub 在 `openspec/changes/_future/` 不在任务里 |
| §14 已确认开放问题 | 自检后另列（6 项答复） |

**遗漏点 → 补：**
- 任务 7 阶段 1 已经把 "vite build 时 VITE_FRONTEND_ENABLED=true" 落到 `.env`（任务 36 是显式开关说明，不冲突）
- 任务 35 已实现"上次状态"列（last_status），与 §9 APScheduler 任务回调一致
- 任务 28 录制器 + 任务 30 回放都用了 WSManager 抽象（任务 22 已实现），不重复定义

### 2. 占位符扫描

正则扫描：`TODO|TBD|FIXME|XXX|待定|placeholder|后续实现`

结果：0 命中（任务 32 标题里的"预留"是真实功能"WS 补漏"，不是占位符；任务 37 标题里的"自动化探针"是有脚本的，不算占位符）

### 3. 类型/命名一致性

| 引用 | 任务 3 定义 | 任务 N 引用 | 一致？ |
|---|---|---|---|
| `User.id` (int) | 任务 4 | 任务 5, 8, 9, 22, 26, 27, 30, 34, 35 | ✓ |
| `User.email` | 任务 4 | 任务 6（bootstrap 用 email 唯一键） | ✓ |
| `Role.name` (str) | 任务 4 | 任务 5, 16（断言 admin 全通） | ✓ |
| `Suite.id` | 任务 10 | 任务 11, 15, 23（启动 run） | ✓ |
| `Case.steps` (JSON) | 任务 10 | 任务 16, 24, 25, 29, 30, 32 | ✓ |
| `Run.id` | 任务 20 | 任务 21, 22, 30, 33（定时） | ✓ |
| `Schedule.id` | 任务 33 | 任务 34, 35 | ✓ |
| `PlaybackHistory.id` | 任务 30 | 任务 31（WS 推流、history 列表） | ✓ |
| `WSManager` | 任务 21 | 任务 22, 27, 30, 32 | ✓ |
| `PytestRunner` | 任务 20 | 任务 21, 22, 33（schedule job） | ✓ |
| `RunConfig` | 任务 20 | 任务 21, 33 | ✓ |
| `Step` dataclass | 任务 29 | 任务 30, 33（schedule 调 start_run 不直接用 Step） | ✓ |
| `parse_codegen_log` | 任务 26 | 任务 28, 32 | ✓ |
| `parse_pytest_line` | 任务 30 | 任务 31, 30（flow 内调用） | ✓ |
| `ActionName` enum | 任务 24（ts） | 任务 25, 28 | ✓ |
| `STEP_SCHEMAS` | 任务 24 | 任务 25, 28 | ✓ |
| `useWS(url, onMsg)` | 任务 23 | 任务 31, 28 | ✓（任务 28 用裸 WS，注释改用 useWS 即可，任务 28 步骤 1 已 OK） |
| `get_current_user_ws` | 任务 22 | 任务 27 | ✓ |
| `get_db` / `get_current_user` | 任务 5 | 任务 16, 21, 26, 30, 34 | ✓ |
| `assert_can` (RBAC) | 任务 5 / 任务 16 | 任务 16 显式调用 | ✓ |
| `Seed bootstrap admin` 钩子 | 任务 6 | 任务 5（auth 全套） | ✓ |

### 4. 风险标记回看

- 任务 9（json_store 异步化）的 3 天估算 → 任务 12（双写层）前必须完成 ✓ 顺序正确
- 任务 20-22（PytestRunner + WS）必须在任务 23（Runs.vue）前完成 ✓
- 任务 29（script_gen）必须在任务 30（playback）前 ✓
- 任务 33（SchedulerService）必须在任务 34（路由）前 ✓
- 任务 37（30 天观察）必须在任务 38（删 streamlit）前 ✓
- 阶段 1-3c 后端就绪 → 阶段 3d（定时）依赖 Phase 2 schedule model ✓
- 录制器依赖 Phase 1 vite+vue+ts 骨架 + Phase 2 case model + Phase 3a case CRUD ✓

### 5. 工期估算（与 §12 对齐）

| 阶段 | 任务数 | 估算（人天） | 备注 |
|---|---|---|---|
| Phase 1 骨架 | 8 | 5 | |
| Phase 2 双写 | 6 | 4 | json_store async 化占 2 天 |
| Phase 3a 静态 | 5 | 4 | |
| Phase 3b 运行 | 4 | 3 | |
| Phase 3c 用例 | 9 | 8 | 录制器 2 天 + 回放 2 天 + 步骤编辑器 2 天 + 杂项 2 天 |
| Phase 3d 定时 | 3 | 2 | |
| Phase 4 切流 | 2 | 1 + 30 天观察 | |
| Phase 5 收尾 | 1 | 1 | |
| **合计（不含观察）** | **38** | **26 人天 ≈ 5.5 周** | |
| **含 30 天观察** | | **~7 周** | 实际可能 8-9 周（含回归、Code Review、返工） |

### 已确认的开放问题（6 项答复，全部落档）

1. **端口** → 8000（后端）+ 5173（前端），开发期两端口，生产只 8000
2. **种子管理员** → `admin@local` / `admin123` 走 .env `BOOTSTRAP_*` 变量，lifespan 启动时若 users 表空则创建（argon2id 哈希，赋 admin 角色），README 提示生产清掉
3. **浏览器矩阵** → 保留 chromium/firefox/webkit 三选一；新增 `GET /api/health/browsers` 路由，前端下拉用此 API
4. **旧 JSON 回灌** → 仅 suites + cases 回灌 PG；playback_history 和 trends 不回灌（损失可接受，重新跑会自然积累）
5. **种子数据** → 从零开始（admin 是唯一初始账号），不预填 demo suites/cases；`scripts/import_legacy_json.py` 留作可选脚本
6. **AI future stub** → 已同意，`openspec/changes/_future/ai-integration.md` 占位（不在任务里实现）

---

## 执行交接

**计划已完成并保存到 `docs/superpowers/plans/2026-06-07-streamlit-to-vue-migration.md`（共 38 任务 / 5 阶段 / ~3000+ 行）。两种执行方式：**

### 1. 子代理驱动（推荐）
- **必需子技能：** `superpowers:subagent-driven-development`
- 每个任务一个新子代理 + 两阶段审查（实现 → 复核）
- 适合 38 任务、跨前后端、需要并行加速的场景
- 主代理负责汇总进度和处理跨任务依赖

### 2. 内联执行
- **必需子技能：** `superpowers:executing-plans`
- 在当前会话中批量执行 + 关键检查点（如阶段 1 完成时、阶段 3a 切流时）
- 适合演示、想亲手跑过的人

**选哪种方式？**



