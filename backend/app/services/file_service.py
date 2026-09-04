from uuid import UUID, uuid4
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.file import File
from app.core.storage import supabase, SUPABASE_STORAGE_BUCKET
from app.models.file import File
from app.models.folder import Folder
from app.schemas.file import (
    InitUploadRequest,
    CompleteUploadRequest,
    ALLOWED_MIME_TYPES,
    MAX_FILE_SIZE,
)


def init_upload(db: Session, data: InitUploadRequest):
    ALLOWED_MIME_TYPES = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/webp",
        "text/plain",
    }

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    if data.size <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must be greater than 0",
        )

    if data.size > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File size cannot exceed 50 MB",
        )

    if data.mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type",
        )

    file_id = str(uuid4())

    safe_filename = (
        data.filename
        .replace("/", "_")
        .replace("\\", "_")
    )

    storage_path = f"uploads/{file_id}/{safe_filename}"

    try:
        result = (
            supabase.storage
            .from_(SUPABASE_STORAGE_BUCKET)
            .create_signed_upload_url(storage_path)
        )

        signed_url = result.get("signedUrl") or result.get("signed_url")
        token = result.get("token")

        if not signed_url or not token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create signed upload URL",
            )

        return {
            "file_id": file_id,
            "storage_path": storage_path,
            "upload_url": signed_url,
            "token": token,
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize upload: {str(e)}",
        )


def upload_to_storage(
    storage_path: str,
    token: str,
    file_bytes: bytes,
    mime_type: str,
):
    try:
        result = (
            supabase.storage
            .from_(SUPABASE_STORAGE_BUCKET)
            .upload_to_signed_url(
                path=storage_path,
                token=token,
                file=file_bytes,
                file_options={
                    "content-type": mime_type,
                },
            )
        )

        return result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file to storage: {str(e)}",
        )


def complete_upload(
    db: Session,
    data: CompleteUploadRequest,
    owner_id: UUID,
):
    try:
        file_id = UUID(data.file_id)

        existing = (
            db.query(File)
            .filter(File.id == file_id)
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="File already exists",
            )

        file = File(
            id=file_id,
            name=data.filename,
            original_name=data.filename,
            mime_type=data.mime_type,
            size=data.size,
            storage_path=data.storage_path,
            owner_id=owner_id,
            folder_id=UUID(data.folder_id) if data.folder_id else None,
            is_deleted=False,
            is_starred=False,
            current_version=1,
        )

        db.add(file)
        db.commit()
        db.refresh(file)

        return file

    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid UUID",
        )
def create_download_url(
    db: Session,
    file_id: UUID,
    user_id: UUID,
):
    from app.models.share import Share

    file = (
        db.query(File)
        .filter(
            File.id == file_id,
            File.is_deleted == False,
        )
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    # Owner always has access.
    has_access = file.owner_id == user_id

    # Direct file share.
    if not has_access:
        direct_share = (
            db.query(Share)
            .filter(
                Share.file_id == file_id,
                Share.shared_with_user_id == user_id,
            )
            .first()
        )

        if direct_share:
            has_access = True

    # Folder share.
    if not has_access and file.folder_id:
        folder_share = (
            db.query(Share)
            .filter(
                Share.folder_id == file.folder_id,
                Share.shared_with_user_id == user_id,
            )
            .first()
        )

        if folder_share:
            has_access = True

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this file",
        )

    try:
        result = (
            supabase.storage
            .from_(SUPABASE_STORAGE_BUCKET)
            .create_signed_url(
                file.storage_path,
                60 * 10,
            )
        )

        signed_url = (
            result.get("signedURL")
            or result.get("signedUrl")
            or result.get("signed_url")
        )

        if not signed_url:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create signed download URL",
            )

        return {
            "file_id": str(file.id),
            "filename": file.name,
            "download_url": signed_url,
            "expires_in": 600,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create download URL: {str(e)}",
        )
def rename_file(
    db: Session,
    file_id: UUID,
    user_id: UUID,
    new_name: str,
):
    file = (
        db.query(File)
        .filter(
            File.id == file_id,
            File.owner_id == user_id,
            File.is_deleted == False,
        )
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    new_name = new_name.strip()

    if not new_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name cannot be empty",
        )

    if len(new_name) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File name cannot exceed 255 characters",
        )

    file.name = new_name

    db.commit()
    db.refresh(file)

    return file


def soft_delete_file(
    db: Session,
    file_id: UUID,
    user_id: UUID,
):
    file = (
        db.query(File)
        .filter(
            File.id == file_id,
            File.owner_id == user_id,
            File.is_deleted == False,
        )
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    file.is_deleted = True
    file.deleted_at = datetime.utcnow()

    db.commit()
    db.refresh(file)

    return file


def restore_file(
    db: Session,
    file_id: UUID,
    user_id: UUID,
):
    file = (
        db.query(File)
        .filter(
            File.id == file_id,
            File.owner_id == user_id,
            File.is_deleted == True,
        )
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deleted file not found",
        )

    file.is_deleted = False
    file.deleted_at = None

    db.commit()
    db.refresh(file)

    return file


def permanent_delete_file(
    db: Session,
    file_id: UUID,
    user_id: UUID,
):
    file = (
        db.query(File)
        .filter(
            File.id == file_id,
            File.owner_id == user_id,
        )
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    try:
        (
            supabase.storage
            .from_(SUPABASE_STORAGE_BUCKET)
            .remove([file.storage_path])
        )

        db.delete(file)
        db.commit()

        return {
            "message": "File permanently deleted",
            "file_id": str(file_id),
        }

    except Exception as e:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to permanently delete file: {str(e)}",
        )
def list_files(db: Session, owner_id: UUID):
    return (
        db.query(File)
        .filter(
            File.owner_id == owner_id,
            File.is_deleted == False,
        )
        .all()
    )
def search_files(
    db: Session,
    owner_id: UUID,
    query: str | None = None,
    mime_type: str | None = None,
    folder_id: UUID | None = None,
    starred: bool | None = None,
):
    filters = [
        File.owner_id == owner_id,
        File.is_deleted == False,
    ]

    if query:
        filters.append(
            File.name.ilike(f"%{query}%")
        )

    if mime_type:
        filters.append(
            File.mime_type == mime_type
        )

    if folder_id:
        filters.append(
            File.folder_id == folder_id
        )

    if starred is not None:
        filters.append(
            File.is_starred == starred
        )

    return (
        db.query(File)
        .filter(*filters)
        .all()
    )
def move_file(
    db: Session,
    file_id: UUID,
    folder_id: UUID | None,
    owner_id: UUID,
):
    file = (
        db.query(File)
        .filter(
            File.id == file_id,
            File.owner_id == owner_id,
            File.is_deleted == False,
        )
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    if folder_id is not None:
        folder = (
            db.query(Folder)
            .filter(
                Folder.id == folder_id,
                Folder.owner_id == owner_id,
                Folder.is_deleted == False,
            )
            .first()
        )

        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Destination folder not found",
            )

    file.folder_id = folder_id

    db.commit()
    db.refresh(file)

    return file
def star_file(
    db: Session,
    file_id: UUID,
    user_id: UUID,
):
    file = (
        db.query(File)
        .filter(
            File.id == file_id,
            File.owner_id == user_id,
            File.is_deleted == False,
        )
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    file.is_starred = True

    db.commit()
    db.refresh(file)

    return file


def unstar_file(
    db: Session,
    file_id: UUID,
    user_id: UUID,
):
    file = (
        db.query(File)
        .filter(
            File.id == file_id,
            File.owner_id == user_id,
        )
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    file.is_starred = False

    db.commit()
    db.refresh(file)

    return file


def list_starred_files(
    db: Session,
    user_id: UUID,
):
    return (
        db.query(File)
        .filter(
            File.owner_id == user_id,
            File.is_starred == True,
            File.is_deleted == False,
        )
        .all()
    )
def list_trash(
    db: Session,
    owner_id: UUID,
):
    return (
        db.query(File)
        .filter(
            File.owner_id == owner_id,
            File.is_deleted == True,
        )
        .all()
    )
def get_file(
    db: Session,
    file_id: UUID,
    owner_id: UUID,
):
    file = (
        db.query(File)
        .filter(
            File.id == file_id,
            File.owner_id == owner_id,
            File.is_deleted == False,
        )
        .first()
    )

    if not file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found",
        )

    return file