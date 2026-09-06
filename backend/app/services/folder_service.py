from uuid import UUID
from datetime import datetime
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.folder import Folder
from app.schemas.folder import FolderCreate, FolderUpdate


def create_folder(
    db: Session,
    data: FolderCreate,
    owner_id: UUID,
):
    if data.parent_id:
        parent = (
            db.query(Folder)
            .filter(
                Folder.id == data.parent_id,
                Folder.owner_id == owner_id,
                Folder.is_deleted == False,
            )
            .first()
        )

        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found",
            )

    existing = (
        db.query(Folder)
        .filter(
            Folder.owner_id == owner_id,
            Folder.parent_id == data.parent_id,
            Folder.name == data.name,
            
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Folder with this name already exists",
        )

    folder = Folder(
        name=data.name,
        parent_id=data.parent_id,
        owner_id=owner_id,
    )

    db.add(folder)
    db.commit()
    db.refresh(folder)

    return folder


def list_folders(
    db: Session,
    owner_id: UUID,
    parent_id: UUID | None = None,
):
    return (
        db.query(Folder)
        .filter(
            Folder.owner_id == owner_id,
            Folder.parent_id == parent_id,
            Folder.is_deleted == False,
        )
        .order_by(Folder.name.asc())
        .all()
    )


def get_folder(
    db: Session,
    folder_id: UUID,
    owner_id: UUID,
):
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
            detail="Folder not found",
        )

    return folder


def update_folder(
    db: Session,
    folder_id: UUID,
    data: FolderUpdate,
    owner_id: UUID,
):
    folder = get_folder(db, folder_id, owner_id)

    if data.name is not None:
        existing = (
            db.query(Folder)
            .filter(
                Folder.owner_id == owner_id,
                Folder.parent_id == (
                    data.parent_id
                    if data.parent_id is not None
                    else folder.parent_id
                ),
                Folder.name == data.name,
                Folder.id != folder_id,
            )
            .first()
        )

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Folder with this name already exists",
            )

        folder.name = data.name

    # Pydantic tracks whether parent_id was explicitly supplied, which lets
    # the API move a folder back to the root with parent_id=null.
    if "parent_id" in data.model_fields_set:
        if data.parent_id == folder_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Folder cannot be its own parent",
            )

        if data.parent_id is not None:
            parent = get_folder(
                db,
                data.parent_id,
                owner_id,
            )

            if parent.id == folder.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid parent folder",
                )

            # Prevent moving a folder inside one of its descendants.
            current = parent
            while current:
                if current.parent_id is None:
                    break
                if current.parent_id == folder.id:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Folder cannot be moved inside its own descendant",
                    )
                current = (
                    db.query(Folder)
                    .filter(
                        Folder.id == current.parent_id,
                        Folder.owner_id == owner_id,
                        Folder.is_deleted == False,
                    )
                    .first()
                )

        folder.parent_id = data.parent_id

    db.commit()
    db.refresh(folder)

    return folder


def delete_folder(
    db: Session,
    folder_id: UUID,
    owner_id: UUID,
):
    folder = get_folder(db, folder_id, owner_id)

    folder.is_deleted = True
    folder.deleted_at = datetime.utcnow()

    db.commit()
    db.refresh(folder)

    return {
        "message": "Folder moved to trash",
        "folder_id": str(folder_id),
    }
def get_folder_breadcrumb(
    db: Session,
    folder_id: UUID,
    owner_id: UUID,
):
    breadcrumb = []

    current = get_folder(
        db=db,
        folder_id=folder_id,
        owner_id=owner_id,
    )

    while current:
        breadcrumb.insert(
            0,
            {
                "id": str(current.id),
                "name": current.name,
            },
        )

        if current.parent_id is None:
            break

        current = (
            db.query(Folder)
            .filter(
                Folder.id == current.parent_id,
                Folder.owner_id == owner_id,
            )
            .first()
        )

        if not current:
            break

    return breadcrumb
def restore_folder(
    db: Session,
    folder_id: UUID,
    owner_id: UUID,
):
    folder = (
        db.query(Folder)
        .filter(
            Folder.id == folder_id,
            Folder.owner_id == owner_id,
            Folder.is_deleted == True,
        )
        .first()
    )

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Deleted folder not found",
        )

    folder.is_deleted = False
    folder.deleted_at = None

    db.commit()
    db.refresh(folder)

    return folder
def permanent_delete_folder(
    db: Session,
    folder_id: UUID,
    owner_id: UUID,
):
    folder = (
        db.query(Folder)
        .filter(
            Folder.id == folder_id,
            Folder.owner_id == owner_id,
        )
        .first()
    )

    if not folder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found",
        )

    db.delete(folder)
    db.commit()

    return {
        "message": "Folder permanently deleted",
        "folder_id": str(folder_id),
    }
def list_deleted_folders(
    db: Session,
    owner_id: UUID,
):
    return (
        db.query(Folder)
        .filter(
            Folder.owner_id == owner_id,
            Folder.is_deleted == True,
        )
        .all()
    )