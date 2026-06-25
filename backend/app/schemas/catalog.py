from pydantic import BaseModel, Field
from datetime import datetime

class SuiteIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    version: str = ""
    description: str = ""

class SuiteOut(BaseModel):
    id: int
    name: str
    version: str
    description: str
    owner_id: int | None
    created_at: datetime
    model_config = {"from_attributes": True}

class Step(BaseModel):
    action: str
    selector: str | None = None
    value: str | None = None
    url: str | None = None
    text: str | None = None
    state: str | None = None
    ms: int | None = None
    name: str | None = None
    x: int | None = None
    y: int | None = None
    code: str | None = None
    expect: str | None = None
    timeout_ms: int | None = None
    note: str | None = None
    model_config = {"extra": "allow"}

class Parameter(BaseModel):
    key: str = ""
    value: str = ""
    description: str = ""

class CaseIn(BaseModel):
    suite_id: int
    name: str = Field(min_length=1, max_length=160)
    tags: list[str] = []
    steps: list[Step] = []
    parameters: list[Parameter] = []

class CaseOut(BaseModel):
    id: int
    suite_id: int
    name: str
    tags: list[str]
    steps: list[Step]
    parameters: list[Parameter] = []
    owner_id: int | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
