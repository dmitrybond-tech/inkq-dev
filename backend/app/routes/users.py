"""User routes."""
from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

# Note: /users/me has been moved to /auth/me for consistency with session-based auth

