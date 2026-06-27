from fastapi import APIRouter, Depends, HTTPException, Query
from app.deps import get_db, get_current_user
from app.schemas.catalog import CaseIn, CaseOut
from app.services import case_service
from app.config import settings
from app.services.script_gen import generate_script

router = APIRouter(prefix="/api/cases", tags=["cases"])


@router.get("", response_model=list[CaseOut])
async def list_(suite_id: int | None = None, db=Depends(get_db), user=Depends(get_current_user)):
    return await case_service.list_cases(db, suite_id=suite_id)


@router.get("/{case_id}", response_model=CaseOut)
async def get(case_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    c = await case_service.get_case(db, case_id)
    if not c:
        raise HTTPException(404, "not found")
    return c


@router.post("", response_model=CaseOut, status_code=201)
async def create(body: CaseIn, db=Depends(get_db), user=Depends(get_current_user)):
    return await case_service.create_case(
        db, suite_id=body.suite_id, name=body.name,
        tags=body.tags, steps=[s.model_dump() for s in body.steps],
        parameters=[p.model_dump() for p in body.parameters],
        owner_id=user.id,
    )


@router.put("/{case_id}", response_model=CaseOut)
async def update(case_id: int, body: CaseIn, db=Depends(get_db), user=Depends(get_current_user)):
    c = await case_service.get_case(db, case_id)
    if not c:
        raise HTTPException(404, "not found")
    return await case_service.update_case_steps(
        db, case_id=case_id,
        steps=[s.model_dump() for s in body.steps],
        parameters=[p.model_dump() for p in body.parameters],
    )


@router.patch("/{case_id}", response_model=CaseOut)
async def patch_case(case_id: int, body: dict, db=Depends(get_db), user=Depends(get_current_user)):
    c = await case_service.get_case(db, case_id)
    if not c:
        raise HTTPException(404, "not found")
    return await case_service.update_case_info(
        db, case_id=case_id,
        name=body["name"],
        version=body.get("version", ""),
    )


@router.delete("/{case_id}", status_code=204)
async def delete(case_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    ok = await case_service.delete_case(db, case_id)
    if not ok:
        raise HTTPException(404, "not found")
    return None


@router.get("/{case_id}/script")
async def script(case_id: int, browser: str = Query("chromium"), db=Depends(get_db), user=Depends(get_current_user)):
    case = await case_service.get_case(db, case_id)
    if not case:
        raise HTTPException(404, "not found")
    return {"script": generate_script(case.name, case.steps or [], browser, breadcrumb=settings.breadcrumb_enabled, parameters=case.parameters or [])}
