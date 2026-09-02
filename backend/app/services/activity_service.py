from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.activity import Activity


def log_activity(
    db: Session,
    user_id: UUID,
    activity_type: str,
    file_id: UUID | None = None,
    folder_id: UUID | None = None,
    metadata: dict | None = None,
):
    activity = Activity(
        user_id=user_id,
        file_id=file_id,
        folder_id=folder_id,
        activity_type=activity_type,
        activity_metadata=metadata,
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity


def list_user_activities(
    db: Session,
    user_id: UUID,
):
    result = db.execute(
        select(Activity)
        .where(Activity.user_id == user_id)
        .order_by(Activity.created_at.desc())
    )

    return result.scalars().all()