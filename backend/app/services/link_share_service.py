from datetime import datetime, timezone
from secrets import token_urlsafe
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.file import File
from app.models.folder import Folder
from app.models.link_share import LinkShare
from app.schemas.link_share import PublicLinkCreate


def create_public_link(
    db: Session,
    data: PublicLinkCreate,
    user_id: UUID,
):
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

    if data.expires_at:
        expires_at = data.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if expires_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Expiry time must be in the future",
            )
    else:
        expires_at = None

    if data.file_id:
        file = (
            db.query(File)
            .filter(
                File.id == data.file_id,
                File.owner_id == user_id,
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
                Folder.owner_id == user_id,
                Folder.is_deleted == False,
            )
            .first()
        )

        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found or not owned by user",
            )

    token = token_urlsafe(32)

    password_hash = None

    if data.password:
        password_hash = hash_password(data.password)

    link = LinkShare(
        file_id=data.file_id,
        folder_id=data.folder_id,
        token=token,
        password_hash=password_hash,
        expires_at=expires_at,
        is_active=True,
        created_by=user_id,
    )

    db.add(link)
    db.commit()
    db.refresh(link)

    return link


def get_public_link(
    db: Session,
    token: str,
):
    link = (
        db.query(LinkShare)
        .filter(
            LinkShare.token == token,
            LinkShare.is_active == True,
        )
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public link not found or inactive",
        )

    if link.expires_at:
        expires_at = link.expires_at

        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(
                tzinfo=timezone.utc
            )

        if expires_at <= datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Public link has expired",
            )

    return link


def access_public_link(
    db: Session,
    token: str,
    password: str | None = None,
):
    link = get_public_link(
        db=db,
        token=token,
    )

    if link.password_hash:
        if not password:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password required",
            )

        if not verify_password(
            password,
            link.password_hash,
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid password",
            )

    if link.file_id:
        file = (
            db.query(File)
            .filter(
                File.id == link.file_id,
                File.is_deleted == False,
            )
            .first()
        )

        if not file:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found",
            )

        return {
            "type": "file",
            "file_id": str(file.id),
            "name": file.name,
            "mime_type": file.mime_type,
            "size": file.size,
            "storage_path": file.storage_path,
        }

    if link.folder_id:
        folder = (
            db.query(Folder)
            .filter(
                Folder.id == link.folder_id,
                Folder.is_deleted == False,
            )
            .first()
        )

        if not folder:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found",
            )

        return {
            "type": "folder",
            "folder_id": str(folder.id),
            "name": folder.name,
        }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Shared resource not found",
    )


def deactivate_public_link(
    db: Session,
    link_id: UUID,
    user_id: UUID,
):
    link = (
        db.query(LinkShare)
        .filter(
            LinkShare.id == link_id,
            LinkShare.created_by == user_id,
        )
        .first()
    )

    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public link not found",
        )

    link.is_active = False

    db.commit()

    return {
        "message": "Public link deactivated successfully"
    }


def list_public_links(
    db: Session,
    user_id: UUID,
):
    return (
        db.query(LinkShare)
        .filter(
            LinkShare.created_by == user_id,
        )
        .all()
    )