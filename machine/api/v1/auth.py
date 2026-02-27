"""
Auth router — minimal backend surface.
All sign-up / sign-in / password reset / social login are handled by Supabase Auth on the frontend.
The backend only exposes:
  - GET /auth/me  → return current user profile + role
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional

from core.utils.get_current_user import get_current_user
from machine.models.users import Users

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/me", response_model=UserProfileResponse, summary="Get current user profile")
async def get_me(current_user: Users = Depends(get_current_user)):
    """
    Returns the authenticated user's profile.
    On first call, a user row is automatically created with role='user'.
    """
    return UserProfileResponse(
        id=str(current_user.id),
        email=current_user.email,
        full_name=current_user.full_name,
        avatar_url=current_user.avatar_url,
        role=current_user.role,
        is_active=current_user.is_active,
    )
