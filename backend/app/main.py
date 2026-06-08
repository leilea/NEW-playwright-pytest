from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import bootstrap_admin
from app.config import settings
from app.db.session import engine
from app.routers import health, auth, suites, cases, dashboard, reports, config, runs


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bootstrap_admin()
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
app.include_router(auth.router)
app.include_router(suites.router)
app.include_router(cases.router)
app.include_router(dashboard.router)
app.include_router(reports.router, prefix="/api")
app.include_router(config.router, prefix="/api")
app.include_router(runs.router, prefix="/api")
