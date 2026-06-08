from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.bootstrap import bootstrap_admin
from app.services.scheduler import scheduler
from app.config import settings
from app.db.session import engine
from app.routers import health, auth, suites, cases, dashboard, reports, config, runs, schedules
from app.ws.run_ws import run_ws
from app.ws.rec_ws import rec_ws
from app.ws.playback_ws import playback_ws


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bootstrap_admin()
    scheduler.start()
    yield
    scheduler.shutdown()
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
app.include_router(schedules.router, prefix="/api")
app.add_websocket_route("/ws/run/{run_id}", run_ws)
app.add_websocket_route("/ws/rec", rec_ws)
app.add_websocket_route("/ws/playback", playback_ws)
