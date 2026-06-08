from fastapi import APIRouter, Depends, HTTPException, Response

from app.deps import get_db, get_current_user
from app.schemas.auth import LoginIn, UserOut
from app.services.auth_service import login_with_password, LoginFailed

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(body: LoginIn, response: Response, db=Depends(get_db)):
    try:
        token, user = await login_with_password(db, email=body.email, password=body.password)
    except LoginFailed:
        raise HTTPException(401, "invalid credentials")
    response.set_cookie("access_token", token, httponly=True, samesite="lax", max_age=8 * 3600)
    return {"access_token": token, "token_type": "bearer"}


@router.get("/me", response_model=UserOut)
async def me(user=Depends(get_current_user), db=Depends(get_db)):
    role_names = [r.role.name for r in user.roles]
    return UserOut(id=user.id, email=user.email, display_name=user.display_name, roles=role_names)


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}
