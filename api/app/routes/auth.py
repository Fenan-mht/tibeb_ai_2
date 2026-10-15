"""Authentication and user profile endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import Settings, get_settings
from app.db.base import get_db
from app.db.models import User

router = APIRouter(tags=["auth"])


class PlanSummary(BaseModel):
    id: str
    name: str
    questions_per_day: int
    monthly_voice_chars: int
    max_upload_chars: int
    cloud_stt: bool


class UserProfileResponse(BaseModel):
    id: str
    phone: str | None
    name: str | None
    grade: int | None
    preferred_lang: str
    plan_id: str
    plan: PlanSummary | None = None
    free_questions_left: int
    created_at: datetime


class TesterItem(BaseModel):
    id: str
    phone: str | None
    name: str | None
    grade: int | None
    preferred_lang: str
    plan_id: str
    free_questions_left: int


@router.get("/v1/me", response_model=UserProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """Return the profile, current plan, and remaining free questions for the active student."""
    plan_summary = None
    if current_user.plan:
        plan_summary = PlanSummary(
            id=current_user.plan.id,
            name=current_user.plan.name,
            questions_per_day=current_user.plan.questions_per_day,
            monthly_voice_chars=current_user.plan.monthly_voice_chars,
            max_upload_chars=current_user.plan.max_upload_chars,
            cloud_stt=current_user.plan.cloud_stt,
        )

    return UserProfileResponse(
        id=current_user.id,
        phone=current_user.phone,
        name=current_user.name,
        grade=current_user.grade,
        preferred_lang=current_user.preferred_lang,
        plan_id=current_user.plan_id,
        plan=plan_summary,
        free_questions_left=current_user.free_questions_left,
        created_at=current_user.created_at,
    )


@router.get("/v1/auth/testers", response_model=list[TesterItem])
def list_available_testers(
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> list[TesterItem]:
    """List available test accounts for the app's tester picker (test mode only)."""
    if settings.AUTH_MODE != "none" and settings.APP_ENV == "production":
        return []

    # Testers are users whose id starts with 'tester-'
    testers = (
        db.query(User)
        .filter(User.id.like("tester-%"))
        .order_by(User.grade.asc(), User.id.asc())
        .all()
    )

    return [
        TesterItem(
            id=u.id,
            phone=u.phone,
            name=u.name,
            grade=u.grade,
            preferred_lang=u.preferred_lang,
            plan_id=u.plan_id,
            free_questions_left=u.free_questions_left,
        )
        for u in testers
    ]
