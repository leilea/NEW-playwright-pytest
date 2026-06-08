import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text

from app.main import app
from app.db.base import Base
import app.models  # noqa: F401


@pytest.fixture
def client():
    return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest.fixture
async def db_session():
    engine = create_async_engine(
        "postgresql+asyncpg://app:app@localhost:5432/dsep_test",
        echo=False,
        connect_args={"timeout": 3},
    )
    Session = async_sessionmaker(engine, expire_on_commit=False)
    async with Session() as session:
        try:
            await session.execute(text("SELECT 1"))
        except Exception:
            pytest.skip("PostgreSQL not available — start with: docker compose up -d postgres")
        try:
            for tbl in ("auth.user_roles", "auth.resource_acls", "auth.users",
                         "catalog.cases", "catalog.suites", "runtime.runs",
                         "runtime.schedules", "auth.roles"):
                try:
                    await session.execute(text(f"DELETE FROM {tbl}"))
                except Exception:
                    pass
            await session.commit()
            yield session
            await session.rollback()
        finally:
            await engine.dispose()
