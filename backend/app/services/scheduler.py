"""SchedulerService — APScheduler + SQLAlchemyJobStore abstraction."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from app.config import settings


class SchedulerService:
    def __init__(self):
        jobstores = {
            "default": SQLAlchemyJobStore(url=settings.database_url.replace("+asyncpg", "+psycopg2"))
        }
        executors = {"default": ThreadPoolExecutor(4)}
        self._scheduler = AsyncIOScheduler(jobstores=jobstores, executors=executors)
        self._started = False

    def start(self):
        if not self._started:
            self._scheduler.start()
            self._started = True

    def add_job(self, job_id: str, func, trigger: str, **kwargs):
        if trigger == "cron":
            parts = kwargs.pop("cron", "* * * * *").split()
            self._scheduler.add_job(
                func, "cron", id=job_id,
                minute=parts[0], hour=parts[1], day=parts[2],
                month=parts[3], day_of_week=parts[4],
                **kwargs,
            )

    def remove_job(self, job_id: str):
        try:
            self._scheduler.remove_job(job_id)
        except Exception:
            pass

    def get_job_ids(self) -> list[str]:
        return [j.id for j in self._scheduler.get_jobs()]

    def shutdown(self):
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False


scheduler = SchedulerService()
