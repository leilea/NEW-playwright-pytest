from pydantic import BaseModel, Field
from datetime import datetime

class SuiteIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""

class SuiteOut(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int | None
    created_at: datetime
    model_config = {"from_attributes": True}

class Step(BaseModel):
    action: str
    selector: str | None = None
    value: str | None = None
    expect: str | None = None
    timeout_ms: int | None = None
    note: str | None = None

class CaseIn(BaseModel):
    suite_id: int
    name: str = Field(min_length=1, max_length=160)
    tags: list[str] = []
    steps: list[Step] = []

class CaseOut(BaseModel):
    id: int
    suite_id: int
    name: str
    tags: list[str]
    steps: list[Step]
    owner_id: int | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
