"""User Pydantic schemas."""
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, field_validator


# Centralized password length constraints for validation
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


# Accept any string here and validate against the AccountType enum
# in app.models.user.AccountType inside the auth.signup endpoint.
AccountType = str


class UserCreate(BaseModel):
    """Schema for user creation (signup)."""
    email: EmailStr
    password: str = Field(...)
    username: str = Field(..., min_length=3, max_length=50)
    account_type: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if not (MIN_PASSWORD_LENGTH <= len(v) <= MAX_PASSWORD_LENGTH):
            raise ValueError(
                f"Password must be between {MIN_PASSWORD_LENGTH} and {MAX_PASSWORD_LENGTH} characters long."
            )
        return v


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    email: str
    username: str
    account_type: str
    onboarding_completed: bool
    avatar_url: str | None = None
    banner_url: str | None = None
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class SignInRequest(BaseModel):
    """Schema for signin request."""
    login: str  # Can be email or username
    password: str

    @field_validator("password")
    @classmethod
    def validate_password_length(cls, v: str) -> str:
        if not (MIN_PASSWORD_LENGTH <= len(v) <= MAX_PASSWORD_LENGTH):
            raise ValueError(
                f"Password must be between {MIN_PASSWORD_LENGTH} and {MAX_PASSWORD_LENGTH} characters long."
            )
        return v


class SignInResponse(BaseModel):
    """Schema for signin response."""
    access_token: str
    user: UserResponse
