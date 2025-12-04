"""Studio profile, residents, booking, and public studio routes."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.artist import Artist
from app.models.artist_studio_resident import ArtistStudioResident
from app.models.booking_request import BookingRequest
from app.models.portfolio import PortfolioImage
from app.models.session import Session as SessionModel
from app.models.studio import Studio
from app.models.user import AccountType, User
from app.routes.auth import get_current_session
from app.schemas.studio import (
    ArtistInvitationsResponse,
    ArtistInvitationItem,
    ArtistInvitationStudio,
    BookingRequestCreate,
    BookingRequestItem,
    BookingRequestListResponse,
    BookingRequestUpdate,
    PublicStudioCard,
    PublicStudioListResponse,
    PublicStudioPortfolioItem,
    PublicStudioResponse,
    PublicStudioTeamMember,
    PublicStudioInfo,
    StudioMeResponse,
    StudioResidentArtist,
    StudioResidentInviteRequest,
    StudioResidentsResponse,
    StudioUpdateRequest,
)


router = APIRouter(prefix="/studios", tags=["studios"])
public_router = APIRouter(prefix="/public/studios", tags=["public_studios"])


def get_current_user(
    session: SessionModel = Depends(get_current_session),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user from session."""
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    return user


def get_or_create_studio(user: User, db: Session) -> Studio:
    """Get the Studio record for a user, creating it if missing."""
    studio = db.query(Studio).filter(Studio.user_id == user.id).first()
    if studio is None:
        studio = Studio(user_id=user.id, name=user.username, slug=user.username)
        db.add(studio)
        db.commit()
        db.refresh(studio)
    # Ensure slug exists for public pages
    if not studio.slug:
        studio.slug = user.username
        db.add(studio)
        db.commit()
        db.refresh(studio)
    return studio


def build_studio_me_response(user: User, studio: Studio) -> StudioMeResponse:
    """Build StudioMeResponse from user and studio models.

    Notes:
    - user.onboarding_completed is the global source of truth for onboarding state.
    - studio.onboarding_completed is kept in sync and is used for public studio visibility.
    """
    return StudioMeResponse(
        username=user.username,
        avatar_url=user.avatar_url,
        banner_url=user.banner_url,
        onboarding_completed=user.onboarding_completed,
        name=studio.name,
        about=studio.about,
        city=studio.city,
        address=studio.address,
        instagram=studio.instagram,
        telegram=studio.telegram,
        vk=studio.vk,
        session_price_label=studio.session_price_label,
    )


@router.get("/me", response_model=StudioMeResponse)
def get_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current authenticated studio profile."""
    if user.account_type != AccountType.STUDIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studios can access this endpoint",
        )

    studio = get_or_create_studio(user, db)

    # Self-healing sync for legacy data:
    # If studio.onboarding_completed is True but user.onboarding_completed is False,
    # promote the user flag to True as the global source of truth.
    if studio.onboarding_completed and not user.onboarding_completed:
        user.onboarding_completed = True
        db.add(user)
        db.commit()
        db.refresh(user)

    return build_studio_me_response(user, studio)


@router.put("/me", response_model=StudioMeResponse)
def update_me(
    payload: StudioUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current authenticated studio profile and onboarding flag."""
    if user.account_type != AccountType.STUDIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studios can access this endpoint",
        )

    studio = get_or_create_studio(user, db)
    data = payload.model_dump(exclude_unset=True)

    onboarding_completed = data.pop("onboarding_completed", None)
    if onboarding_completed is not None:
        flag = bool(onboarding_completed)
        studio.onboarding_completed = flag
        user.onboarding_completed = flag

    for field, value in data.items():
        setattr(studio, field, value)

    db.add(user)
    db.add(studio)
    db.commit()
    db.refresh(user)
    db.refresh(studio)

    return build_studio_me_response(user, studio)


@router.get("/me/residents", response_model=StudioResidentsResponse)
def list_residents(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List residents (artists) for the current studio."""
    if user.account_type != AccountType.STUDIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studios can access this endpoint",
        )

    studio = get_or_create_studio(user, db)
    rows: List[ArtistStudioResident] = (
        db.query(ArtistStudioResident)
        .filter(ArtistStudioResident.studio_id == studio.id)
        .order_by(ArtistStudioResident.created_at.desc())
        .all()
    )

    items: List[StudioResidentArtist] = []
    for res in rows:
        artist = db.query(Artist).filter(Artist.id == res.artist_id).first()
        if not artist:
            continue
        artist_user = db.query(User).filter(User.id == artist.user_id).first()
        if not artist_user:
            continue
        items.append(
            StudioResidentArtist(
                id=artist.id,
                username=artist_user.username,
                display_name=artist.display_name,
                avatar_url=artist_user.avatar_url,
                styles=list(artist.styles or []),
                status=res.status,  # type: ignore[arg-type]
                created_at=res.created_at,
            )
        )

    return StudioResidentsResponse(items=items)


@router.post(
    "/me/residents/invite",
    response_model=ArtistInvitationItem,
    status_code=status.HTTP_201_CREATED,
)
def invite_resident(
    payload: StudioResidentInviteRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Invite an artist (by username or email) to become a resident."""
    if user.account_type != AccountType.STUDIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studios can access this endpoint",
        )

    studio = get_or_create_studio(user, db)
    identifier = payload.identifier.strip()
    if not identifier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Identifier is required",
        )

    artist_user = (
        db.query(User)
        .filter(
            User.account_type == AccountType.ARTIST,
            (User.username == identifier) | (User.email == identifier),
        )
        .first()
    )
    if not artist_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )

    artist = db.query(Artist).filter(Artist.user_id == artist_user.id).first()
    if artist is None:
        artist = Artist(user_id=artist_user.id)
        db.add(artist)
        db.commit()
        db.refresh(artist)

    resident = (
        db.query(ArtistStudioResident)
        .filter(
            ArtistStudioResident.studio_id == studio.id,
            ArtistStudioResident.artist_id == artist.id,
        )
        .first()
    )
    if resident is None:
        resident = ArtistStudioResident(
            studio_id=studio.id,
            artist_id=artist.id,
            status="invited",
        )
        db.add(resident)
    else:
        resident.status = "invited"

    db.commit()
    db.refresh(resident)

    return ArtistInvitationItem(
        id=resident.id,
        studio=ArtistInvitationStudio(
            id=studio.id,
            name=studio.name,
            city=studio.city,
        ),
        status=resident.status,  # type: ignore[arg-type]
        created_at=resident.created_at,
    )


@router.get("/me/booking-requests", response_model=BookingRequestListResponse)
def list_booking_requests(
    status_param: Optional[str] = Query(
        default=None,
        alias="status",
        description="Optional status filter: new, in_progress, closed",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List booking requests for the current studio."""
    if user.account_type != AccountType.STUDIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studios can access this endpoint",
        )

    studio = get_or_create_studio(user, db)
    query = db.query(BookingRequest).filter(BookingRequest.studio_id == studio.id)
    if status_param:
        if status_param not in ("new", "in_progress", "closed"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status filter",
            )
        query = query.filter(BookingRequest.status == status_param)

    rows = query.order_by(BookingRequest.created_at.desc()).all()

    items = [
        BookingRequestItem(
            id=row.id,
            studio_id=row.studio_id,
            artist_id=row.artist_id,
            type=row.type,  # type: ignore[arg-type]
            client_name=row.client_name,
            client_contact=row.client_contact,
            comment=row.comment,
            status=row.status,  # type: ignore[arg-type]
            created_at=row.created_at,
        )
        for row in rows
    ]
    return BookingRequestListResponse(items=items)


@router.patch(
    "/me/booking-requests/{request_id}",
    response_model=BookingRequestItem,
)
def update_booking_request(
    request_id: int,
    payload: BookingRequestUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update status of a booking request owned by the current studio."""
    if user.account_type != AccountType.STUDIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studios can access this endpoint",
        )

    studio = get_or_create_studio(user, db)
    request = (
        db.query(BookingRequest)
        .filter(
            BookingRequest.id == request_id,
            BookingRequest.studio_id == studio.id,
        )
        .first()
    )
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking request not found",
        )

    request.status = payload.status
    db.add(request)
    db.commit()
    db.refresh(request)

    return BookingRequestItem(
        id=request.id,
        studio_id=request.studio_id,
        artist_id=request.artist_id,
        type=request.type,  # type: ignore[arg-type]
        client_name=request.client_name,
        client_contact=request.client_contact,
        comment=request.comment,
        status=request.status,  # type: ignore[arg-type]
        created_at=request.created_at,
    )


@public_router.post(
    "/{studio_slug}/booking",
    response_model=BookingRequestItem,
    status_code=status.HTTP_201_CREATED,
)
def create_public_booking_request(
    studio_slug: str = Path(..., description="Studio slug/username"),
    payload: BookingRequestCreate = ...,
    db: Session = Depends(get_db),
):
    """Public endpoint for creating a booking request for a studio."""
    # Resolve studio by user.username (primary) or Studio.slug as fallback
    user = (
        db.query(User)
        .filter(
            User.username == studio_slug,
            User.account_type == AccountType.STUDIO,
        )
        .first()
    )
    studio: Optional[Studio] = None
    if user:
        studio = db.query(Studio).filter(Studio.user_id == user.id).first()
    else:
        studio = db.query(Studio).filter(Studio.slug == studio_slug).first()

    if not studio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio not found",
        )

    artist_id: Optional[int] = None
    if payload.type == "artist_specific":
        if payload.artist_id is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="artist_id is required for artist_specific bookings",
            )
        # Validate artist is an accepted resident
        residency = (
            db.query(ArtistStudioResident)
            .filter(
                ArtistStudioResident.studio_id == studio.id,
                ArtistStudioResident.artist_id == payload.artist_id,
                ArtistStudioResident.status == "accepted",
            )
            .first()
        )
        if residency is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Artist is not an accepted resident of this studio",
            )
        artist_id = payload.artist_id

    request = BookingRequest(
        studio_id=studio.id,
        artist_id=artist_id,
        type=payload.type,
        client_name=payload.client_name,
        client_contact=payload.client_contact,
        comment=payload.comment,
        status="new",
    )
    db.add(request)
    db.commit()
    db.refresh(request)

    return BookingRequestItem(
        id=request.id,
        studio_id=request.studio_id,
        artist_id=request.artist_id,
        type=request.type,  # type: ignore[arg-type]
        client_name=request.client_name,
        client_contact=request.client_contact,
        comment=request.comment,
        status=request.status,  # type: ignore[arg-type]
        created_at=request.created_at,
    )


@public_router.get(
    "/{studio_slug}",
    response_model=PublicStudioResponse,
)
def get_public_studio(
    studio_slug: str = Path(..., description="Studio slug/username"),
    db: Session = Depends(get_db),
):
    """Get public studio page data by slug/username.
    
    Only returns studios who have completed onboarding.
    """
    user = (
        db.query(User)
        .filter(
            User.username == studio_slug,
            User.account_type == AccountType.STUDIO,
        )
        .first()
    )
    studio: Optional[Studio] = None
    if user:
        studio = db.query(Studio).filter(Studio.user_id == user.id).first()
    else:
        studio = db.query(Studio).filter(Studio.slug == studio_slug).first()

    if not studio or (user is None and studio.user_id is None):
        # If studio exists without a linked user or no match at all, treat as not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio not found",
        )

    if user is None:
        # Resolve user from studio.user_id
        user = db.query(User).filter(User.id == studio.user_id).first()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio not found",
        )
    
    # Keep studio.onboarding_completed in sync for public visibility.
    # If the user has completed onboarding but the studio flag is False,
    # promote the studio flag so that public visibility matches global state.
    if user.onboarding_completed and not studio.onboarding_completed:
        studio.onboarding_completed = True
        db.add(studio)
        db.commit()
        db.refresh(studio)

    # Check if studio has completed onboarding
    if not studio.onboarding_completed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio not found",
        )

    # Gallery based on portfolio images for the studio's user
    images: List[PortfolioImage] = (
        db.query(PortfolioImage)
        .filter(PortfolioImage.user_id == user.id)
        .all()
    )
    gallery_items: List[PublicStudioPortfolioItem] = [
        PublicStudioPortfolioItem(
            id=img.id,
            image_url=img.url,
            width=img.width,
            height=img.height,
        )
        for img in images
        if img.kind == "portfolio"
    ]

    # Team: accepted residents only
    residencies: List[ArtistStudioResident] = (
        db.query(ArtistStudioResident)
        .filter(
            ArtistStudioResident.studio_id == studio.id,
            ArtistStudioResident.status == "accepted",
        )
        .all()
    )
    team: List[PublicStudioTeamMember] = []
    style_set: set[str] = set()
    for res in residencies:
        artist = db.query(Artist).filter(Artist.id == res.artist_id).first()
        if not artist:
            continue
        artist_user = db.query(User).filter(User.id == artist.user_id).first()
        if not artist_user:
            continue
        styles_list = list(artist.styles or [])
        for style in styles_list:
            style_set.add(style)
        team.append(
            PublicStudioTeamMember(
                artist_id=artist.id,
                username=artist_user.username,
                display_name=artist.display_name,
                avatar_url=artist_user.avatar_url,
                styles=styles_list,
            )
        )

    studio_info = PublicStudioInfo(
        name=studio.name or user.username,
        about=studio.about,
        city=studio.city,
        address=studio.address,
        instagram=studio.instagram,
        telegram=studio.telegram,
        vk=studio.vk,
        session_price_label=studio.session_price_label,
    )

    return PublicStudioResponse(
        studio=studio_info,
        username=user.username,
        avatar_url=user.avatar_url,
        banner_url=user.banner_url,
        gallery=gallery_items,
        team=team,
        aggregated_styles=sorted(style_set),
    )


@public_router.get("", response_model=PublicStudioListResponse)
def list_public_studios(
    db: Session = Depends(get_db),
    city: Optional[str] = Query(default=None, description="Filter by city (case-insensitive)"),
    limit: int = Query(default=16, ge=1, le=48),
    offset: int = Query(default=0, ge=0),
) -> PublicStudioListResponse:
    """List public studios with optional city filter.

    Only returns studios whose associated user has completed onboarding.
    """
    base_query = (
        db.query(User, Studio)
        .join(Studio, Studio.user_id == User.id)
        .filter(
            User.account_type == AccountType.STUDIO,
            User.onboarding_completed == True,  # noqa: E712
        )
    )

    if city:
        city_normalized = city.strip().lower()
        if city_normalized:
            base_query = base_query.filter(func.lower(Studio.city) == city_normalized)

    total = base_query.count()

    rows = (
        base_query.order_by(Studio.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    items: List[PublicStudioCard] = []
    for user, studio in rows:
        slug = studio.slug or user.username
        if not studio.slug:
            studio.slug = user.username
            db.add(studio)
        items.append(
            PublicStudioCard(
                id=studio.id,
                username=user.username,
                slug=slug,
                name=studio.name or studio.display_name,
                city=studio.city,
                session_price_label=studio.session_price_label,
                avatar_url=user.avatar_url,
                banner_url=user.banner_url,
            )
        )

    db.commit()

    return PublicStudioListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


