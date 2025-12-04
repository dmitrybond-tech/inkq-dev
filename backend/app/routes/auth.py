"""Authentication routes."""
import secrets
from datetime import datetime, timedelta
from hashlib import sha256

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import or_

from app.db.base import get_db
from app.config import settings
from app.models.user import User, AccountType
from app.models.artist import Artist
from app.models.studio import Studio
from app.models.model import Model
from app.models.session import Session as SessionModel
from app.schemas.user import UserCreate, UserResponse, SignInRequest, SignInResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Password hashing configuration.
# We implement password hashing using:
# - A SHA-256 pre-hash of the UTF-8 encoded password to produce a fixed-size
#   32-byte digest.
# - Direct bcrypt hashing of that digest, using a configurable number of rounds.
# This mirrors the security properties of bcrypt_sha256 without relying on
# passlib, and ensures we never hit bcrypt's 72-byte input limit for raw
# passwords.
BCRYPT_ROUNDS: int = 12

# Security scheme for Bearer token
security = HTTPBearer(auto_error=False)


def _password_digest(plain_password: str) -> bytes:
    """Return a fixed-size SHA-256 digest for the given plain-text password.

    This protects us from bcrypt's 72-byte input limit and ensures that the
    underlying hash function always receives a constant-size input derived
    from the UTF-8 encoding of the password.
    """
    return sha256(plain_password.encode("utf-8")).digest()


def hash_password(password: str) -> str:
    """Hash a password using SHA-256 pre-hash + bcrypt.

    The function returns a UTF-8 string representation of the bcrypt hash
    suitable for storage in the database.
    """
    digest: bytes = _password_digest(password)
    salt: bytes = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
    hashed: bytes = bcrypt.hashpw(digest, salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a stored bcrypt hash.

    Returns True if the password matches, False otherwise. If the stored hash
    is malformed or incompatible with bcrypt, this function returns False
    instead of raising, so that callers can safely treat it as invalid
    credentials.
    """
    digest: bytes = _password_digest(plain_password)
    try:
        return bcrypt.checkpw(digest, hashed_password.encode("utf-8"))
    except ValueError:
        # Malformed hash or unsupported format
        return False


def create_role_for_user(db: Session, user: User, account_type: str):
    """Create the appropriate role entity for a user based on account_type."""
    if account_type == "artist":
        artist = Artist(user_id=user.id, slug=user.username)
        db.add(artist)
    elif account_type == "studio":
        studio = Studio(user_id=user.id)
        db.add(studio)
    elif account_type == "model":
        model = Model(user_id=user.id)
        db.add(model)
    else:
        raise ValueError(f"Invalid account_type: {account_type}")


def create_session(db: Session, user: User, ip_address: str | None = None, user_agent: str | None = None) -> SessionModel:
    """Create a new session for a user.
    
    Generates a secure random token and sets expires_at based on
    settings.access_token_expire_minutes.
    
    Args:
        db: Database session
        user: User to create session for
        ip_address: Optional IP address of the client
        user_agent: Optional user agent string
        
    Returns:
        The created SessionModel instance
    """
    token = secrets.token_urlsafe(32)
    now = datetime.utcnow()
    expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    
    session = SessionModel(
        id=token,
        user_id=user.id,
        created_at=now,
        expires_at=expires_at,
        last_seen_at=now,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def signup(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user account with the specified role.
    
    This endpoint:
    - Validates account_type (must be artist, studio, or model)
    - Creates User + corresponding role in a single transaction
    - Enforces 1-1 relationship invariant
    """
    # Validate account_type
    try:
        account_type_enum = AccountType(user_data.account_type)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid account_type. Must be one of: artist, studio, model"
        )
    
    # Create user and role in a single transaction
    try:
        # Hash password with safe helper; map any hashing-related issues to 4xx.
        # We intentionally do not leak low-level bcrypt error messages to the
        # client. Any unexpected error during hashing is treated as an invalid
        # password rather than a 500 response.
        try:
            password_hash = hash_password(user_data.password)
        except Exception as e:
            # Do not leak low-level bcrypt messages to the client.
            msg = str(e)
            if "password cannot be longer than 72 bytes" in msg.lower():
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="Invalid password",
                )
            # For any other hashing error, also treat it as a client-side
            # password problem rather than a 500.
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Invalid password",
            )

        # Create user
        user = User(
            email=user_data.email,
            password_hash=password_hash,
            username=user_data.username,
            account_type=account_type_enum,
            onboarding_completed=False,
        )
        db.add(user)
        db.flush()  # Flush to get user.id without committing
        
        # Create corresponding role
        create_role_for_user(db, user, user_data.account_type)
        
        # Commit transaction
        db.commit()
        db.refresh(user)

        return UserResponse.model_validate(user)

    except HTTPException:
        db.rollback()
        # Re-raise HTTPException instances produced above (e.g. invalid
        # password) without changing their status codes or details.
        raise
    except IntegrityError as e:
        db.rollback()
        # Check if it's a unique constraint violation
        if "email" in str(e.orig).lower() or "unique" in str(e.orig).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email or username already exists"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


def get_current_session(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db)
) -> SessionModel:
    """Dependency to get current session from Bearer token or inkq_session cookie.

    Primary source of truth is the Bearer token in the Authorization header,
    which is what tests and documented API expect. For convenience, we also
    support falling back to the ``inkq_session`` cookie when the header is
    missing. This does not change the public contract, but makes it easier
    for browser clients that rely on cookies.
    
    Implements sliding window: on successful validation, updates expires_at
    to now + settings.access_token_expire_minutes.
    """
    token: str | None = None

    # Prefer Authorization: Bearer <token> header when provided
    if credentials is not None:
        token = credentials.credentials

    # Fallback to inkq_session cookie if no Authorization header is present
    if not token:
        token = request.cookies.get("inkq_session")

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token",
        )

    session = db.query(SessionModel).filter(SessionModel.id == token).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token"
        )
    
    # Check expiration
    now = datetime.utcnow()
    if session.expires_at < now:
        db.delete(session)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization token"
        )
    
    # Sliding window: refresh expires_at on valid requests
    new_expires_at = now + timedelta(minutes=settings.access_token_expire_minutes)
    session.expires_at = new_expires_at
    session.last_seen_at = now
    db.commit()
    db.refresh(session)
    
    return session


@router.post("/signin", response_model=SignInResponse, status_code=status.HTTP_200_OK)
def signin(
    signin_data: SignInRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Sign in a user and create a session.
    
    Accepts login (email or username) and password.
    Returns access_token and user data.
    """
    # Find user by email or username (case-insensitive for email)
    user = db.query(User).filter(
        or_(
            User.email.ilike(signin_data.login),
            User.username == signin_data.login
        )
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials"
        )
    
    # Verify password
    if not verify_password(signin_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid_credentials"
        )
    
    # Extract IP and user agent
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    # Create session using helper function
    session = create_session(db, user, ip_address=ip_address, user_agent=user_agent)
    
    return SignInResponse(
        access_token=session.id,
        user=UserResponse.model_validate(user)
    )


@router.get("/me", response_model=UserResponse)
def get_current_user(
    session: SessionModel = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user.
    
    Requires valid session token in Authorization header.
    Session expiry is refreshed automatically by get_current_session (sliding window).
    """
    
    # Load user
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Enforce role invariants
    if user.account_type == AccountType.ARTIST and user.artist is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data integrity error: User with account_type=artist has no artist record"
        )
    if user.account_type == AccountType.STUDIO and user.studio is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data integrity error: User with account_type=studio has no studio record"
        )
    if user.account_type == AccountType.MODEL and user.model is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Data integrity error: User with account_type=model has no model record"
        )
    
    return UserResponse.model_validate(user)


@router.post("/signout", status_code=status.HTTP_204_NO_CONTENT)
def signout(
    session: SessionModel = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """
    Sign out the current user by deleting their session.
    
    Returns 204 No Content (idempotent).
    """
    db.delete(session)
    db.commit()
    return None

