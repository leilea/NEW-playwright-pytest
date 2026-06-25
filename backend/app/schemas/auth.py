from pydantic import BaseModel


class LoginIn(BaseModel):
    email: str
    password: str


class UserOut(BaseModel):
    id: int
    email: str
    display_name: str | None
    roles: list[str]
    model_config = {"from_attributes": True}
