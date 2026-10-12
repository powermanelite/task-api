from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


MAX_TITLE_LENGTH = 200


def _require_non_blank(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValueError("title must not be blank")
    return value


class Task(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    title: str
    description: str | None = None
    completed: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class TaskCreate(BaseModel):
    title: str = Field(max_length=MAX_TITLE_LENGTH)
    description: str | None = None
    completed: bool = False

    _check_title = field_validator("title")(_require_non_blank)


class TaskUpdate(BaseModel):
    """Partial update: only fields present in the request body are applied."""

    title: str | None = Field(default=None, max_length=MAX_TITLE_LENGTH)
    description: str | None = None
    completed: bool | None = None

    @field_validator("title")
    @classmethod
    def _check_title(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("title must not be null")
        return _require_non_blank(value)

    @field_validator("completed")
    @classmethod
    def _check_completed(cls, value: bool | None) -> bool:
        if value is None:
            raise ValueError("completed must not be null")
        return value


class TaskPage(BaseModel):
    total: int
    limit: int
    offset: int
    next_offset: int | None
    previous_offset: int | None
    items: list[Task]
