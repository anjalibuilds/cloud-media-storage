from uuid import uuid4

from sqlalchemy import Column, String, DateTime, ForeignKey, UUID
from sqlalchemy.sql import func

from app.core.database import Base


class Share(Base):
    __tablename__ = "shares"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

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

    owner_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    shared_with_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )

    role = Column(
        String(20),
        nullable=False,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )