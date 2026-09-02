from pydantic import BaseModel, Field


from pydantic import BaseModel, Field, field_validator
from typing import Optional


ALLOWED_MIME_TYPES = {
    "application/pdf",

    # Images
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",

    # Videos
    "video/mp4",
    "video/webm",
    "video/quicktime",

    # Audio
    "audio/mpeg",
    "audio/wav",
    "audio/ogg",

    # Documents
    "text/plain",
    "application/json",
}


MAX_FILE_SIZE = 50 * 1024 * 1024


class InitUploadRequest(BaseModel):
    filename: str = Field(..., min_length=1, max_length=255)
    mime_type: str
    size: int = Field(..., gt=0)

    @field_validator("mime_type")
    @classmethod
    def validate_mime_type(cls, value: str):
        if value not in ALLOWED_MIME_TYPES:
            raise ValueError(f"Unsupported file type: {value}")
        return value

    @field_validator("size")
    @classmethod
    def validate_file_size(cls, value: int):
        if value > MAX_FILE_SIZE:
            raise ValueError("File size cannot exceed 50 MB")
        return value


class InitUploadResponse(BaseModel):
    file_id: str
    storage_path: str
    upload_url: str
    token: str

class CompleteUploadRequest(BaseModel):
    file_id: str
    storage_path: str
    filename: str = Field(min_length=1, max_length=255)
    mime_type: str = Field(min_length=1, max_length=255)
    size: int = Field(gt=0)
    folder_id: str | None = None


class FileResponse(BaseModel):
    id: str
    name: str
    original_name: str
    mime_type: str
    size: int
    storage_path: str
    owner_id: str
    folder_id: str | None
    is_deleted: bool
    is_starred: bool
    current_version: int