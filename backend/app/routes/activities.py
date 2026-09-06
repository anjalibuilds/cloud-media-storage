from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.services.activity_service import list_user_activities


router = APIRouter(
    prefix="/activities",
    tags=["Activities"],
)


@router.get("")
def get_activities(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    activities = list_user_activities(
        db=db,
        user_id=current_user.id,
    )

    return {
        "activities": [
            {
                "id": str(activity.id),
                "activity_type": activity.activity_type,
                "file_id": (
                    str(activity.file_id)
                    if activity.file_id
                    else None
                ),
                "folder_id": (
                    str(activity.folder_id)
                    if activity.folder_id
                    else None
                ),
                "metadata": activity.activity_metadata,
                "created_at": activity.created_at.isoformat(),
            }
            for activity in activities
        ]
    }