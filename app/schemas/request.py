from enum import Enum
from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class RequestStatus(str, Enum):
    new = "new"
    progress = "progress"
    closed = "closed"


class RequestCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    equipment_id: int
    description: str = Field(min_length=1, max_length=2048)


class RequestPatch(BaseModel):
    """Правка инженером своей заявки: диагноз, работы, перевод в «Закрыта»."""

    model_config = ConfigDict(populate_by_name=True)

    status: Optional[RequestStatus] = None
    diagnosis: Optional[str] = Field(None, max_length=2048)
    work_done: Optional[str] = Field(
        None,
        max_length=2048,
        validation_alias=AliasChoices("workDone", "work_done"),
        serialization_alias="workDone",
    )


class RequestAssign(BaseModel):
    engineer_id: int


class RequestOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    equipment: str
    department: str
    description: str
    reporter: str
    reporter_department: str
    engineer_id: Optional[int] = None
    engineer: Optional[str] = None
    status: str
    updated: str
    diagnosis: Optional[str] = None
    work_done: Optional[str] = Field(None, serialization_alias="workDone")
