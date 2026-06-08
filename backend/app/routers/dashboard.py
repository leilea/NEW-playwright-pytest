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
        if status in buckets[k]:
            buckets[k][status] += 1
    return [{"date": k, **v} for k, v in sorted(buckets.items())]
