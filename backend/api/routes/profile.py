"""API routes for user profile and configuration."""
from fastapi import APIRouter, Depends

from backend.schemas.models import UserProfile, PublicConfig
from backend.core.config import get_settings
from backend.services.auth import get_current_user_id, build_user_profile

router = APIRouter(prefix="/api", tags=["profile"])


@router.get("/me", response_model=UserProfile)
async def get_current_user(user_id: str = Depends(get_current_user_id)) -> UserProfile:
    """Get current authenticated user's profile."""
    return UserProfile(**build_user_profile(user_id))


@router.get("/config/public", response_model=PublicConfig)
async def get_public_config() -> PublicConfig:
    """
    Get public configuration that can be safely sent to the frontend.

    This endpoint returns only client-safe configuration like Firebase API keys
    and OAuth client IDs. Private keys are never exposed.
    """
    settings = get_settings()
    config = settings.get_public_config()
    return PublicConfig(**config)
