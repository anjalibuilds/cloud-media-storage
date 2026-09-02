from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.folder import (
    FolderCreate,
    FolderUpdate,
    FolderResponse,
)
from app.services.folder_service import (
    create_folder,
    list_folders,
    get_folder,
    update_folder,
    delete_folder,
    get_folder_breadcrumb,
    restore_folder,
    permanent_delete_folder,
    list_deleted_folders,
)


router = APIRouter(
    prefix="/folders",
    tags=["Folders"],
)


# =========================
# CREATE FOLDER
# =========================

@router.post(
    "",
    response_model=FolderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_folder_route(
    data: FolderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_folder(
        db=db,
        data=data,
        owner_id=current_user.id,
    )


# =========================
# LIST FOLDERS
# =========================

@router.get(
    "",
    response_model=list[FolderResponse],
)
def list_folder_route(
    parent_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_folders(
        db=db,
        owner_id=current_user.id,
        parent_id=parent_id,
    )


# =========================
# FOLDER BREADCRUMB
# IMPORTANT: before /{folder_id}
# =========================

@router.get(
    "/{folder_id}/breadcrumb"
)
def folder_breadcrumb_route(
    folder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_folder_breadcrumb(
        db=db,
        folder_id=folder_id,
        owner_id=current_user.id,
    )


# =========================
# FOLDER TRASH
# IMPORTANT: before /{folder_id}
# =========================

@router.get(
    "/trash"
)
def folder_trash_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    folders = list_deleted_folders(
        db=db,
        owner_id=current_user.id,
    )

    return {
        "folders": [
            {
                "id": str(folder.id),
                "name": folder.name,
                "parent_id": (
                    str(folder.parent_id)
                    if folder.parent_id
                    else None
                ),
                "is_deleted": folder.is_deleted,
                "deleted_at": (
                    folder.deleted_at.isoformat()
                    if folder.deleted_at
                    else None
                ),
            }
            for folder in folders
        ]
    }


# =========================
# GET FOLDER
# =========================

@router.get(
    "/{folder_id}",
    response_model=FolderResponse,
)
def get_folder_route(
    folder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_folder(
        db=db,
        folder_id=folder_id,
        owner_id=current_user.id,
    )


# =========================
# UPDATE / RENAME FOLDER
# =========================

@router.patch(
    "/{folder_id}",
    response_model=FolderResponse,
)
def update_folder_route(
    folder_id: UUID,
    data: FolderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_folder(
        db=db,
        folder_id=folder_id,
        data=data,
        owner_id=current_user.id,
    )


# =========================
# SOFT DELETE FOLDER
# =========================

@router.delete(
    "/{folder_id}",
)
def delete_folder_route(
    folder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delete_folder(
        db=db,
        folder_id=folder_id,
        owner_id=current_user.id,
    )


# =========================
# RESTORE FOLDER
# =========================

@router.post(
    "/restore/{folder_id}",
    response_model=FolderResponse,
)
def restore_folder_route(
    folder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return restore_folder(
        db=db,
        folder_id=folder_id,
        owner_id=current_user.id,
    )


# =========================
# PERMANENT DELETE FOLDER
# =========================

@router.delete(
    "/permanent/{folder_id}"
)
def permanently_delete_folder_route(
    folder_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return permanent_delete_folder(
        db=db,
        folder_id=folder_id,
        owner_id=current_user.id,
    )