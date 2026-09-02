from uuid import UUID

from pydantic import BaseModel, EmailStr, Field


class ShareCreate(BaseModel):
    file_id: UUID | None = None
    folder_id: UUID | None = None
    email: EmailStr
    role: str = Field(..., pattern="^(viewer|editor)$")


class ShareResponse(BaseModel):
    id: UUID
    file_id: UUID | None
    folder_id: UUID | None
    owner_id: UUID
    shared_with_user_id: UUID
    role: str

    class Config:
        from_attributes = True