from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class FolderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    parent_id: UUID | None = None


class FolderUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )
    parent_id: UUID | None = None


class FolderResponse(BaseModel):
    id: UUID
    owner_id: UUID
    parent_id: UUID | None
    name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True