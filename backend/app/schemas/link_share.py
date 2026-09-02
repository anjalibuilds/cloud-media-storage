from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field


class PublicLinkCreate(BaseModel):
    file_id: UUID | None = None
    folder_id: UUID | None = None
    expires_at: datetime | None = None
    password: str | None = Field(
        default=None,
        min_length=4,
        max_length=100,
    )


class PublicLinkResponse(BaseModel):
    id: UUID
    file_id: UUID | None
    folder_id: UUID | None
    token: str
    expires_at: datetime | None
    is_active: bool
    created_by: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class PublicLinkAccessRequest(BaseModel):
    password: str | None = None