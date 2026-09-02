from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, UUID
from sqlalchemy.sql import func

from app.core.database import Base


class LinkShare(Base):
    __tablename__ = "link_shares"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    file_id = Column(
        UUID(as_uuid=True),
        ForeignKey("files.id"),
        nullable=True,
    )

    folder_id = Column(
        UUID(as_uuid=True),
        ForeignKey("folders.id"),
        nullable=True,
    )

    token = Column(
        String(255),
        unique=True,
        nullable=False,
    )

    password_hash = Column(
        String(255),
        nullable=True,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_by = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )