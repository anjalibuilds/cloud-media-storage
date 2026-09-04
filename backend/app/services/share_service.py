from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.share import Share
from app.models.user import User
from app.models.file import File
from app.models.folder import Folder
from app.schemas.share import ShareCreate


VALID_ROLES = {"viewer", "editor"}


def create_share(
    db: Session,
    data: ShareCreate,
    owner_id: UUID,
):
    if data.role not in VALID_ROLES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role",
        )

    if not data.file_id and not data.folder_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either file_id or folder_id is required",
        )

    if data.file_id and data.folder_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Share either a file or a folder, not both",
        )

    target_user = (
        db.query(User)
        .filter(User.email == data.email)
        .first()
    )

    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if target_user.id == owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot share with yourself",
        )

    if data.file_id:
        file = (
            db.query(File)
            .filter(
                File.id == data.file_id,
                File.owner_id == owner_id,
                File.is_deleted == False,
            )
            .first()
        )

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found or not owned by user",
            )

    if data.folder_id:
        folder = (
            db.query(Folder)
            .filter(
                Folder.id == data.folder_id,
                Folder.owner_id == owner_id,
                Folder.is_deleted == False,
            )
            .first()
        )

        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found or not owned by user",
            )

    existing_query = db.query(Share).filter(
        Share.owner_id == owner_id,
        Share.shared_with_user_id == target_user.id,
    )

    if data.file_id:
        existing_query = existing_query.filter(
            Share.file_id == data.file_id
        )

    if data.folder_id:
        existing_query = existing_query.filter(
            Share.folder_id == data.folder_id
        )

    existing = existing_query.first()

    if existing:
        existing.role = data.role
        db.commit()
        db.refresh(existing)
        return existing

    share = Share(
        file_id=data.file_id,
        folder_id=data.folder_id,
        owner_id=owner_id,
        shared_with_user_id=target_user.id,
        role=data.role,
    )

    db.add(share)
    db.commit()
    db.refresh(share)

    return share


def list_my_shares(
    db: Session,
    user_id: UUID,
):
    shares = (
        db.query(Share)
        .filter(
            Share.shared_with_user_id == user_id
        )
        .all()
    )

    result = []

    for share in shares:
        item = {
            "id": str(share.id),
            "file_id": str(share.file_id) if share.file_id else None,
            "folder_id": str(share.folder_id) if share.folder_id else None,
            "owner_id": str(share.owner_id),
            "shared_with_user_id": str(share.shared_with_user_id),
            "role": share.role,
        }

        owner = (
            db.query(User)
            .filter(User.id == share.owner_id)
            .first()
        )

        item["owner_email"] = owner.email if owner else None
        item["owner_name"] = owner.full_name if owner else None

        if share.file_id:
            file = (
                db.query(File)
                .filter(File.id == share.file_id)
                .first()
            )

            if file:
                item["name"] = file.name
                item["original_name"] = file.original_name
                item["mime_type"] = file.mime_type
                item["size"] = file.size
                item["storage_path"] = file.storage_path
                item["is_deleted"] = file.is_deleted

        if share.folder_id:
            folder = (
                db.query(Folder)
                .filter(Folder.id == share.folder_id)
                .first()
            )

            if folder:
                item["name"] = folder.name
                item["is_deleted"] = folder.is_deleted

        result.append(item)

    return result


def delete_share(
    db: Session,
    share_id: UUID,
    owner_id: UUID,
):
    share = (
        db.query(Share)
        .filter(
            Share.id == share_id,
            Share.owner_id == owner_id,
        )
        .first()
    )

    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Share not found",
        )

    db.delete(share)
    db.commit()

    return {
        "message": "Share removed successfully"
    }


def get_permission(
    db: Session,
    user_id: UUID,
    file_id: UUID | None = None,
    folder_id: UUID | None = None,
):
    if file_id:
        file = (
            db.query(File)
            .filter(File.id == file_id)
            .first()
        )

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        if file.owner_id == user_id:
            return "owner"

        share = (
            db.query(Share)
            .filter(
                Share.file_id == file_id,
                Share.shared_with_user_id == user_id,
            )
            .first()
        )

        if share:
            return share.role

        if file.folder_id:
            folder_share = (
                db.query(Share)
                .filter(
                    Share.folder_id == file.folder_id,
                    Share.shared_with_user_id == user_id,
                )
                .first()
            )

            if folder_share:
                return folder_share.role

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this file",
        )

    if folder_id:
        folder = (
            db.query(Folder)
            .filter(Folder.id == folder_id)
            .first()
        )

        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found",
            )

        if folder.owner_id == user_id:
            return "owner"

        share = (
            db.query(Share)
            .filter(
                Share.folder_id == folder_id,
                Share.shared_with_user_id == user_id,
            )
            .first()
        )

        if share:
            return share.role

        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to access this folder",
        )

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="File or folder is required",
    )