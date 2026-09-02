from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.share import ShareCreate, ShareResponse
from app.services.share_service import (
    create_share,
    list_my_shares,
    delete_share,
    get_permission,
)
from app.schemas.link_share import (
    PublicLinkCreate,
    PublicLinkAccessRequest,
    PublicLinkResponse,
)

from app.services.link_share_service import (
    create_public_link,
    access_public_link,
    deactivate_public_link,
    list_public_links,
)


router = APIRouter(
    prefix="/shares",
    tags=["Sharing"],
)


@router.post(
    "",
    response_model=ShareResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_share_route(
    data: ShareCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_share(
        db=db,
        data=data,
        owner_id=current_user.id,
    )


@router.get(
    "",
    response_model=list[ShareResponse],
)
def list_shares_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_my_shares(
        db=db,
        user_id=current_user.id,
    )


@router.get("/permission")
def get_permission_route(
    file_id: UUID | None = None,
    folder_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    permission = get_permission(
        db=db,
        user_id=current_user.id,
        file_id=file_id,
        folder_id=folder_id,
    )

    return {
        "permission": permission
    }


@router.delete("/{share_id}")
def delete_share_route(
    share_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return delete_share(
        db=db,
        share_id=share_id,
        owner_id=current_user.id,
    )
# =========================
# PUBLIC SHAREABLE LINK
# =========================

@router.post(
    "/public-link",
    response_model=PublicLinkResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_public_link_route(
    data: PublicLinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_public_link(
        db=db,
        data=data,
        user_id=current_user.id,
    )


@router.get(
    "/public-links",
    response_model=list[PublicLinkResponse],
)
def list_public_links_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_public_links(
        db=db,
        user_id=current_user.id,
    )


@router.post(
    "/public-link/{token}/access",
)
def access_public_link_route(
    token: str,
    data: PublicLinkAccessRequest,
    db: Session = Depends(get_db),
):
    return access_public_link(
        db=db,
        token=token,
        password=data.password,
    )


@router.delete(
    "/public-link/{link_id}",
)
def deactivate_public_link_route(
    link_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return deactivate_public_link(
        db=db,
        link_id=link_id,
        user_id=current_user.id,
    )