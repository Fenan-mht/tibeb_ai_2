"""Authentication and identity dependencies for Tibeb API."""

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.config import Settings, get_settings
from app.db.base import get_db
from app.db.models import User


def get_current_user(
    x_tester_id: str | None = Header(None, alias="X-Tester-Id"),
    authorization: str | None = Header(None, alias="Authorization"),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> User:
    """Resolve the currently authenticated student user.

    In test mode (AUTH_MODE=none), authentication is bypassed by checking the
    X-Tester-Id header against seeded tester accounts.
    In production mode (AUTH_MODE=jwt), Bearer JWT tokens are verified.
    """
    if settings.AUTH_MODE == "none":
        if not x_tester_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing X-Tester-Id header in test auth mode",
                headers={"WWW-Authenticate": "TesterId"},
            )

        # Lookup user by ID or phone in database
        user = (
            db.query(User)
            .options(joinedload(User.plan))
            .filter((User.id == x_tester_id) | (User.phone == x_tester_id))
            .first()
        )
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Unknown tester ID: '{x_tester_id}'",
                headers={"WWW-Authenticate": "TesterId"},
            )

        return user

    # Production JWT verification mode
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # JWT token decoding logic will be verified in Step 4/Phase 3 auth
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="JWT authentication will be enabled in Phase 3",
    )
