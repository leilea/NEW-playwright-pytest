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
