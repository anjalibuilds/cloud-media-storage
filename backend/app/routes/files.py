from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    status,
    UploadFile,
    File as FastAPIFile,
)
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.file import (
    InitUploadRequest,
    InitUploadResponse,
    CompleteUploadRequest,
)
from app.services.file_service import (
    upload_to_storage,
    init_upload,
    complete_upload,
    create_download_url,
    rename_file,
    soft_delete_file,
    restore_file,
    permanent_delete_file,
    list_files,
    search_files,
    move_file,
    star_file,
    unstar_file,
    list_starred_files,
    list_trash,
    get_file,
)


router = APIRouter(
    prefix="/files",
    tags=["Files"],
)


# =========================
# UPLOAD
# =========================

@router.post(
    "/init-upload",
    response_model=InitUploadResponse,
)
def initialize_upload(
    data: InitUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return init_upload(db, data)


@router.post("/upload")
async def upload_file(
    storage_path: str,
    token: str,
    mime_type: str,
    file: UploadFile = FastAPIFile(...),
    current_user: User = Depends(get_current_user),
):
    file_bytes = await file.read()

    if not file_bytes:
        return {
            "message": "Uploaded file is empty"
        }

    upload_to_storage(
        storage_path=storage_path,
        token=token,
        file_bytes=file_bytes,
        mime_type=mime_type,
    )

    return {
        "message": "File uploaded to storage successfully",
        "storage_path": storage_path,
        "size": len(file_bytes),
    }


@router.post(
    "/complete-upload",
    status_code=status.HTTP_201_CREATED,
)
def complete_file_upload(
    data: CompleteUploadRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = complete_upload(
        db=db,
        data=data,
        owner_id=current_user.id,
    )

    return {
        "message": "File upload completed successfully",
        "file": {
            "id": str(file.id),
            "name": file.name,
            "original_name": file.original_name,
            "mime_type": file.mime_type,
            "size": file.size,
            "storage_path": file.storage_path,
            "owner_id": str(file.owner_id),
            "folder_id": (
                str(file.folder_id)
                if file.folder_id
                else None
            ),
            "is_deleted": file.is_deleted,
            "is_starred": file.is_starred,
            "current_version": file.current_version,
        },
    }


# =========================
# FILE LIST / SEARCH
# =========================

@router.get("")
def get_files(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    files = list_files(
        db=db,
        owner_id=current_user.id,
    )

    return {
        "files": [
            {
                "id": str(file.id),
                "name": file.name,
                "original_name": file.original_name,
                "mime_type": file.mime_type,
                "size": file.size,
                "storage_path": file.storage_path,
                "folder_id": (
                    str(file.folder_id)
                    if file.folder_id
                    else None
                ),
                "is_deleted": file.is_deleted,
                "is_starred": file.is_starred,
                "current_version": file.current_version,
            }
            for file in files
        ]
    }


@router.get("/search")
def search_file_list(
    query: str | None = None,
    mime_type: str | None = None,
    folder_id: UUID | None = None,
    starred: bool | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    files = search_files(
        db=db,
        owner_id=current_user.id,
        query=query,
        mime_type=mime_type,
        folder_id=folder_id,
        starred=starred,
    )

    return {
        "files": [
            {
                "id": str(file.id),
                "name": file.name,
                "original_name": file.original_name,
                "mime_type": file.mime_type,
                "size": file.size,
                "storage_path": file.storage_path,
                "folder_id": (
                    str(file.folder_id)
                    if file.folder_id
                    else None
                ),
                "is_deleted": file.is_deleted,
                "is_starred": file.is_starred,
                "current_version": file.current_version,
            }
            for file in files
        ]
    }

    return {
        "files": [
            {
                "id": str(file.id),
                "name": file.name,
                "original_name": file.original_name,
                "mime_type": file.mime_type,
                "size": file.size,
                "storage_path": file.storage_path,
                "folder_id": (
                    str(file.folder_id)
                    if file.folder_id
                    else None
                ),
                "is_deleted": file.is_deleted,
                "is_starred": file.is_starred,
                "current_version": file.current_version,
            }
            for file in files
        ]
    }


@router.get("/starred")
def starred_files_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    files = list_starred_files(
        db=db,
        user_id=current_user.id,
    )

    return {
        "files": [
            {
                "id": str(file.id),
                "name": file.name,
                "mime_type": file.mime_type,
                "size": file.size,
                "folder_id": (
                    str(file.folder_id)
                    if file.folder_id
                    else None
                ),
                "is_starred": file.is_starred,
            }
            for file in files
        ]
    }


@router.get("/trash")
def get_trash(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    files = list_trash(
        db=db,
        owner_id=current_user.id,
    )

    return {
        "files": [
            {
                "id": str(file.id),
                "name": file.name,
                "original_name": file.original_name,
                "mime_type": file.mime_type,
                "size": file.size,
                "storage_path": file.storage_path,
                "folder_id": (
                    str(file.folder_id)
                    if file.folder_id
                    else None
                ),
                "is_deleted": file.is_deleted,
                "deleted_at": (
                    file.deleted_at.isoformat()
                    if file.deleted_at
                    else None
                ),
            }
            for file in files
        ]
    }


# =========================
# FILE DETAILS / DOWNLOAD
# =========================

@router.get("/download/{file_id}")
def download_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_download_url(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
    )


@router.get("/{file_id}")
def get_file_details(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = get_file(
        db=db,
        file_id=file_id,
        owner_id=current_user.id,
    )

    return {
        "id": str(file.id),
        "name": file.name,
        "original_name": file.original_name,
        "mime_type": file.mime_type,
        "size": file.size,
        "storage_path": file.storage_path,
        "owner_id": str(file.owner_id),
        "folder_id": (
            str(file.folder_id)
            if file.folder_id
            else None
        ),
        "is_deleted": file.is_deleted,
        "is_starred": file.is_starred,
        "current_version": file.current_version,
    }


# =========================
# RENAME / MOVE
# =========================

@router.patch("/rename/{file_id}")
def rename_file_route(
    file_id: UUID,
    new_name: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = rename_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
        new_name=new_name,
    )

    return {
        "message": "File renamed successfully",
        "file_id": str(file.id),
        "name": file.name,
    }


@router.patch("/move/{file_id}")
def move_file_route(
    file_id: UUID,
    folder_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = move_file(
        db=db,
        file_id=file_id,
        folder_id=folder_id,
        owner_id=current_user.id,
    )

    return {
        "message": "File moved successfully",
        "file_id": str(file.id),
        "folder_id": (
            str(file.folder_id)
            if file.folder_id
            else None
        ),
    }


# =========================
# STAR / UNSTAR
# =========================

@router.post("/star/{file_id}")
def star_file_route(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = star_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
    )

    return {
        "message": "File starred successfully",
        "file_id": str(file.id),
    }


@router.delete("/star/{file_id}")
def unstar_file_route(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = unstar_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
    )

    return {
        "message": "File unstarred successfully",
        "file_id": str(file.id),
    }


# =========================
# TRASH / RESTORE / DELETE
# =========================

@router.delete("/{file_id}")
def delete_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = soft_delete_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
    )

    return {
        "message": "File moved to trash",
        "file_id": str(file.id),
    }


@router.post("/restore/{file_id}")
def restore_deleted_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = restore_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
    )

    return {
        "message": "File restored successfully",
        "file_id": str(file.id),
    }


@router.delete("/permanent/{file_id}")
def permanently_delete_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return permanent_delete_file(
        db=db,
        file_id=file_id,
        user_id=current_user.id,
    )