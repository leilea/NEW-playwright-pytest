from fastapi import APIRouter, Depends, HTTPException
from app.deps import get_db, get_current_user
from app.schemas.catalog import SuiteIn, SuiteOut
from app.services import suite_service
from app.security.rbac import assert_can

router = APIRouter(prefix="/api/suites", tags=["suites"])


@router.get("", response_model=list[SuiteOut])
async def list_(db=Depends(get_db), user=Depends(get_current_user)):
    return await suite_service.list_suites(db)


@router.get("/{suite_id}", response_model=SuiteOut)
async def get(suite_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    s = await suite_service.get_suite(db, suite_id)
    if not s:
        raise HTTPException(404, "not found")
    return s


@router.post("", response_model=SuiteOut, status_code=201)
async def create(body: SuiteIn, db=Depends(get_db), user=Depends(get_current_user)):
    return await suite_service.create_suite(db, name=body.name, version=body.version, description=body.description, owner_id=user.id)


@router.put("/{suite_id}", response_model=SuiteOut)
async def update(suite_id: int, body: SuiteIn, db=Depends(get_db), user=Depends(get_current_user)):
    s = await suite_service.get_suite(db, suite_id)
    if not s:
        raise HTTPException(404, "not found")
    await assert_can(user, "write", ("suite", suite_id), db)
    return await suite_service.update_suite(db, suite_id, name=body.name, version=body.version, description=body.description)


@router.delete("/{suite_id}", status_code=204)
async def delete(suite_id: int, db=Depends(get_db), user=Depends(get_current_user)):
    s = await suite_service.get_suite(db, suite_id)
    if not s:
        raise HTTPException(404, "not found")
    await assert_can(user, "delete", ("suite", suite_id), db)
    await suite_service.delete_suite(db, suite_id)
    return None
