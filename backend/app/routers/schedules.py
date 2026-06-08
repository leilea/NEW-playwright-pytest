from fastapi import APIRouter, Depends, HTTPException
from app.deps import get_current_user
from app.services.scheduler import scheduler

router = APIRouter(prefix="/api/schedules", tags=["schedules"])


@router.get("")
async def list_(user=Depends(get_current_user)):
    return [{"id": jid} for jid in scheduler.get_job_ids()]


@router.post("/{schedule_id}/trigger")
async def trigger(schedule_id: str, user=Depends(get_current_user)):
    return {"ok": True, "schedule_id": schedule_id, "triggered": True}
