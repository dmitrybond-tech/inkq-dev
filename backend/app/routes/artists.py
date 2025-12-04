"""Artist profile and public artist routes."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.user import User, AccountType
from app.models.artist_studio_resident import ArtistStudioResident
from app.models.artist import Artist
from app.models.portfolio import PortfolioImage
from app.models.session import Session as SessionModel
from app.routes.auth import get_current_session
from app.schemas.artist import (
    ArtistMeResponse,
    ArtistOnboardingStepStatus,
    ArtistUpdateRequest,
    ArtistStudioShort,
    PortfolioItem,
    PublicArtistResponse,
    PublicArtistCard,
    PublicArtistFiltersResponse,
    PublicArtistListResponse,
    PublicArtistStyle,
)
from app.schemas.media import PortfolioImageResponse, PortfolioListResponse
from app.schemas.studio import ArtistInvitationsResponse, ArtistInvitationItem, ArtistInvitationStudio

router = APIRouter(prefix="/artists", tags=["artists"])
public_router = APIRouter(prefix="/public/artists", tags=["public_artists"])


AVAILABLE_STYLES: List[PublicArtistStyle] = [
    PublicArtistStyle(id="traditional", label_en="Traditional", label_ru="Традиционный"),
    PublicArtistStyle(id="neo_traditional", label_en="Neo-traditional", label_ru="Нео-традиционный"),
    PublicArtistStyle(id="blackwork", label_en="Blackwork", label_ru="Блэкворк"),
    PublicArtistStyle(id="realism", label_en="Realism", label_ru="Реализм"),
    PublicArtistStyle(id="watercolor", label_en="Watercolor", label_ru="Акварель"),
    PublicArtistStyle(id="geometric", label_en="Geometric", label_ru="Геометрия"),
    PublicArtistStyle(id="minimalist", label_en="Minimalist", label_ru="Минимализм"),
]


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


def get_or_create_artist(user: User, db: Session) -> Artist:
    """Get the Artist record for a user, creating it if missing."""
    artist = db.query(Artist).filter(Artist.user_id == user.id).first()
    if artist is None:
        artist = Artist(user_id=user.id, slug=user.username)
        db.add(artist)
        db.commit()
        db.refresh(artist)
    # Ensure slug exists for public pages
    if not artist.slug:
        artist.slug = user.username
        db.add(artist)
        db.commit()
        db.refresh(artist)
    # Ensure styles is always a list
    if artist.styles is None:
        artist.styles = []
    return artist


def compute_onboarding_steps(user: User, artist: Artist, db: Session) -> ArtistOnboardingStepStatus:
    """Compute onboarding step completion for an artist."""
    # Portfolio images
    images: List[PortfolioImage] = (
        db.query(PortfolioImage)
        .filter(PortfolioImage.user_id == user.id)
        .all()
    )
    portfolio_count = sum(1 for img in images if img.kind == "portfolio")
    wannado_count = sum(1 for img in images if img.kind == "wannado")

    # Steps completion
    styles_list = artist.styles or []
    about_complete = bool((artist.about or "").strip()) and bool((artist.city or "").strip()) and len(styles_list) >= 1
    media_complete = bool(user.avatar_url) and bool(user.banner_url)
    portfolio_complete = portfolio_count >= 3

    # Wannado is optional: treat as complete even if empty
    wannado_complete = wannado_count >= 1 or True

    # Determine first incomplete step
    if not about_complete:
        first_incomplete_step = 1
    elif not media_complete:
        first_incomplete_step = 2
    elif not portfolio_complete:
        first_incomplete_step = 3
    elif not wannado_complete:
        first_incomplete_step = 4
    else:
        # All complete, default to last step
        first_incomplete_step = 4

    return ArtistOnboardingStepStatus(
        about_complete=about_complete,
        media_complete=media_complete,
        portfolio_complete=portfolio_complete,
        wannado_complete=wannado_complete,
        first_incomplete_step=first_incomplete_step,
    )


def build_artist_me_response(user: User, artist: Artist, db: Session) -> ArtistMeResponse:
    """Build ArtistMeResponse from user and artist models."""
    steps = compute_onboarding_steps(user, artist, db)

    return ArtistMeResponse(
        username=user.username,
        avatar_url=user.avatar_url,
        banner_url=user.banner_url,
        onboarding_completed=user.onboarding_completed,
        about=artist.about,
        styles=list(artist.styles or []),
        city=artist.city,
        studio_id=artist.studio_id,
        session_price=artist.session_price,
        instagram=artist.instagram,
        telegram=artist.telegram,
        steps=steps,
    )


def build_artist_studios_list(artist: Artist, db: Session) -> List[ArtistStudioShort]:
    """Build list of studios where artist has accepted membership."""
    from app.models.studio import Studio  # local import to avoid circular

    residencies: List[ArtistStudioResident] = (
        db.query(ArtistStudioResident)
        .filter(
            ArtistStudioResident.artist_id == artist.id,
            ArtistStudioResident.status == "accepted",
        )
        .all()
    )

    studios: List[ArtistStudioShort] = []
    for res in residencies:
        studio = db.query(Studio).filter(Studio.id == res.studio_id).first()
        if not studio:
            continue

        studio_user = db.query(User).filter(User.id == studio.user_id).first()
        if not studio_user:
            continue

        # Use studio name or display_name, fallback to username
        display_name = studio.name or studio.display_name or studio_user.username
        slug = studio.slug or studio_user.username

        studios.append(
            ArtistStudioShort(
                id=studio.id,
                slug=slug,
                display_name=display_name,
                avatar_url=studio_user.avatar_url,
            )
        )

    return studios


@router.get("/me", response_model=ArtistMeResponse)
def get_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current authenticated artist profile and onboarding status."""
    if user.account_type != AccountType.ARTIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only artists can access this endpoint",
        )

    artist = get_or_create_artist(user, db)
    return build_artist_me_response(user, artist, db)


@router.put("/me", response_model=ArtistMeResponse)
def update_me(
    payload: ArtistUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current authenticated artist profile and onboarding flag."""
    if user.account_type != AccountType.ARTIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only artists can access this endpoint",
        )

    artist = get_or_create_artist(user, db)

    data = payload.model_dump(exclude_unset=True)

    # Handle onboarding_completed on user
    onboarding_completed = data.pop("onboarding_completed", None)
    if onboarding_completed is not None:
        user.onboarding_completed = bool(onboarding_completed)

    # Update artist fields
    for field, value in data.items():
        if field == "styles" and value is None:
            value = []
        setattr(artist, field, value)

    db.add(user)
    db.add(artist)
    db.commit()
    db.refresh(user)
    db.refresh(artist)

    return build_artist_me_response(user, artist, db)


@router.get("/me/invitations", response_model=ArtistInvitationsResponse)
def list_my_invitations(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List studio invitations for current artist."""
    if user.account_type != AccountType.ARTIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only artists can access this endpoint",
        )

    artist = get_or_create_artist(user, db)
    rows: List[ArtistStudioResident] = (
        db.query(ArtistStudioResident)
        .filter(ArtistStudioResident.artist_id == artist.id)
        .order_by(ArtistStudioResident.created_at.desc())
        .all()
    )

    items: List[ArtistInvitationItem] = []
    for res in rows:
        from app.models.studio import Studio  # local import to avoid circular

        studio_obj = db.query(Studio).filter(Studio.id == res.studio_id).first()
        if not studio_obj:
            continue
        studio_user = db.query(User).filter(User.id == studio_obj.user_id).first()
        if not studio_user:
            continue

        items.append(
            ArtistInvitationItem(
                id=res.id,
                studio=ArtistInvitationStudio(
                    id=studio_obj.id,
                    name=studio_obj.name,
                    city=studio_obj.city,
                ),
                status=res.status,  # type: ignore[arg-type]
                created_at=res.created_at,
            )
        )

    return ArtistInvitationsResponse(items=items)


def _update_invitation_status(
    artist: Artist,
    invitation_id: int,
    new_status: str,
    db: Session,
) -> ArtistInvitationItem:
    """Shared helper for updating invitation status."""
    from app.models.studio import Studio  # local import to avoid circular

    invitation = (
        db.query(ArtistStudioResident)
        .filter(
            ArtistStudioResident.id == invitation_id,
            ArtistStudioResident.artist_id == artist.id,
        )
        .first()
    )
    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )
    if invitation.status != "invited":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only invitations with status 'invited' can be updated",
        )

    invitation.status = new_status
    db.add(invitation)
    db.commit()
    db.refresh(invitation)

    studio = db.query(Studio).filter(Studio.id == invitation.studio_id).first()
    if not studio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio not found",
        )
    studio_user = db.query(User).filter(User.id == studio.user_id).first()
    if not studio_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Studio user not found",
        )

    return ArtistInvitationItem(
        id=invitation.id,
        studio=ArtistInvitationStudio(
            id=studio.id,
            name=studio.name,
            city=studio.city,
        ),
        status=invitation.status,  # type: ignore[arg-type]
        created_at=invitation.created_at,
    )


@router.post(
    "/me/invitations/{invitation_id}/accept",
    response_model=ArtistInvitationItem,
)
def accept_invitation(
    invitation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Accept a studio invitation."""
    if user.account_type != AccountType.ARTIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only artists can access this endpoint",
        )
    artist = get_or_create_artist(user, db)
    return _update_invitation_status(artist, invitation_id, "accepted", db)


@router.post(
    "/me/invitations/{invitation_id}/reject",
    response_model=ArtistInvitationItem,
)
def reject_invitation(
    invitation_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Reject a studio invitation."""
    if user.account_type != AccountType.ARTIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only artists can access this endpoint",
        )
    artist = get_or_create_artist(user, db)
    return _update_invitation_status(artist, invitation_id, "rejected", db)


@router.get("/{username}", response_model=PublicArtistResponse)
def get_public_artist(
    username: str = Path(..., description="Artist username"),
    db: Session = Depends(get_db),
):
    """Get public artist profile by username."""
    user = (
        db.query(User)
        .filter(
            User.username == username,
            User.account_type == AccountType.ARTIST,
        )
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )

    artist = db.query(Artist).filter(Artist.user_id == user.id).first()
    if artist is None:
        # Create an empty artist record to preserve invariants
        artist = Artist(user_id=user.id, slug=user.username)
        db.add(artist)
        db.commit()
        db.refresh(artist)

    images: List[PortfolioImage] = (
        db.query(PortfolioImage)
        .filter(PortfolioImage.user_id == user.id)
        .all()
    )

    portfolio_items: List[PortfolioItem] = [
        PortfolioItem(
            id=img.id,
            url=img.url,
            width=img.width,
            height=img.height,
            kind=img.kind,  # type: ignore[arg-type]
            title=img.title,
            description=img.description,
            approx_price=img.approx_price,
            placement=img.placement,
        )
        for img in images
        if img.kind == "portfolio"
    ]
    wannado_items: List[PortfolioItem] = [
        PortfolioItem(
            id=img.id,
            url=img.url,
            width=img.width,
            height=img.height,
            kind=img.kind,  # type: ignore[arg-type]
            title=img.title,
            description=img.description,
            approx_price=img.approx_price,
            placement=img.placement,
        )
        for img in images
        if img.kind == "wannado"
    ]

    studios_list = build_artist_studios_list(artist, db)

    return PublicArtistResponse(
        username=user.username,
        about=artist.about,
        styles=list(artist.styles or []),
        city=artist.city,
        session_price=artist.session_price,
        instagram=artist.instagram,
        telegram=artist.telegram,
        avatar_url=user.avatar_url,
        banner_url=user.banner_url,
        portfolio=portfolio_items,
        wannado=wannado_items,
        studios=studios_list,
    )


@public_router.get("", response_model=PublicArtistListResponse)
def list_public_artists(
    db: Session = Depends(get_db),
    city: Optional[str] = Query(default=None, description="Filter by city (case-insensitive)"),
    styles: Optional[str] = Query(
        default=None,
        description="Comma-separated list of style IDs (e.g. 'traditional,blackwork')",
    ),
    limit: int = Query(default=16, ge=1, le=48),
    offset: int = Query(default=0, ge=0),
) -> PublicArtistListResponse:
    """List public artists with optional city and style filters.
    
    Only returns artists who have completed onboarding (onboarding_completed=True).
    """
    try:
        base_query = (
            db.query(User, Artist)
            .join(Artist, Artist.user_id == User.id)
            .filter(
                User.account_type == AccountType.ARTIST,
                User.onboarding_completed == True,
            )
        )

        if city:
            city_normalized = city.strip().lower()
            if city_normalized:
                base_query = base_query.filter(func.lower(Artist.city) == city_normalized)

        style_ids: List[str] = []
        if styles:
            style_ids = [s.strip() for s in styles.split(",") if s.strip()]
            if style_ids:
                # Filter artists that have ANY of the requested styles (OR logic)
                style_filters = [Artist.styles.contains([style_id]) for style_id in style_ids]
                base_query = base_query.filter(or_(*style_filters))

        total = base_query.count()

        rows = (
            base_query.order_by(Artist.created_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )

        items: List[PublicArtistCard] = []
        for user, artist in rows:
            # Ensure slug exists, fallback to username
            slug = artist.slug or user.username
            if not artist.slug:
                artist.slug = user.username
                db.add(artist)
            items.append(
                PublicArtistCard(
                    id=user.id,
                    username=user.username,
                    slug=slug,
                    display_name=artist.display_name,
                    city=artist.city,
                    styles=list(artist.styles or []),
                    price_from=artist.session_price,
                    price_currency="EUR",
                    avatar_url=user.avatar_url,
                    banner_url=user.banner_url,
                )
            )
        db.commit()

        return PublicArtistListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )
    except Exception as e:
        # Log the error for debugging but return a clean error response
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Error in list_public_artists: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load artists: {str(e)}",
        )


@public_router.get("/filters", response_model=PublicArtistFiltersResponse)
def get_public_artist_filters(
    db: Session = Depends(get_db),
) -> PublicArtistFiltersResponse:
    """Get available filters (cities and styles) for public artists catalog.
    
    Only includes cities from artists who have completed onboarding.
    """
    try:
        city_rows = (
            db.query(Artist.city)
            .join(User, Artist.user_id == User.id)
            .filter(
                User.account_type == AccountType.ARTIST,
                User.onboarding_completed == True,
                Artist.city.isnot(None),
                func.length(func.trim(Artist.city)) > 0,
            )
            .distinct()
            .order_by(Artist.city)
            .all()
        )

        cities = [row[0] for row in city_rows if row[0] is not None]

        return PublicArtistFiltersResponse(cities=cities, styles=AVAILABLE_STYLES)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.exception("Error in get_public_artist_filters: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load filters: {str(e)}",
        )


@public_router.get("/{slug}", response_model=PublicArtistResponse)
def get_public_artist_by_slug(
    slug: str = Path(..., description="Artist slug"),
    db: Session = Depends(get_db),
):
    """Get public artist profile by slug.
    
    Only returns artists who have completed onboarding.
    """
    # Try to find by slug first, then fallback to username for backward compatibility
    artist = (
        db.query(Artist)
        .join(User, Artist.user_id == User.id)
        .filter(
            or_(Artist.slug == slug, User.username == slug),
            User.account_type == AccountType.ARTIST,
            User.onboarding_completed == True,
        )
        .first()
    )
    
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )
    
    user = db.query(User).filter(User.id == artist.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )
    
    # Ensure slug is set
    if not artist.slug:
        artist.slug = user.username
        db.add(artist)
        db.commit()
        db.refresh(artist)
    
    images: List[PortfolioImage] = (
        db.query(PortfolioImage)
        .filter(PortfolioImage.user_id == user.id)
        .all()
    )

    portfolio_items: List[PortfolioItem] = [
        PortfolioItem(
            id=img.id,
            url=img.url,
            width=img.width,
            height=img.height,
            kind=img.kind,  # type: ignore[arg-type]
            title=img.title,
            description=img.description,
            approx_price=img.approx_price,
            placement=img.placement,
        )
        for img in images
        if img.kind == "portfolio"
    ]
    wannado_items: List[PortfolioItem] = [
        PortfolioItem(
            id=img.id,
            url=img.url,
            width=img.width,
            height=img.height,
            kind=img.kind,  # type: ignore[arg-type]
            title=img.title,
            description=img.description,
            approx_price=img.approx_price,
            placement=img.placement,
        )
        for img in images
        if img.kind == "wannado"
    ]

    studios_list = build_artist_studios_list(artist, db)

    return PublicArtistResponse(
        username=user.username,
        about=artist.about,
        styles=list(artist.styles or []),
        city=artist.city,
        session_price=artist.session_price,
        instagram=artist.instagram,
        telegram=artist.telegram,
        avatar_url=user.avatar_url,
        banner_url=user.banner_url,
        portfolio=portfolio_items,
        wannado=wannado_items,
        studios=studios_list,
    )


@public_router.get("/{slug}/portfolio", response_model=PortfolioListResponse)
def get_public_artist_portfolio(
    slug: str = Path(..., description="Artist slug"),
    db: Session = Depends(get_db),
):
    """Get public portfolio items for an artist by slug."""
    artist = (
        db.query(Artist)
        .join(User, Artist.user_id == User.id)
        .filter(
            or_(Artist.slug == slug, User.username == slug),
            User.account_type == AccountType.ARTIST,
            User.onboarding_completed == True,
        )
        .first()
    )
    
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )
    
    images = (
        db.query(PortfolioImage)
        .filter(
            PortfolioImage.user_id == artist.user_id,
            PortfolioImage.kind == "portfolio",
        )
        .order_by(PortfolioImage.created_at.desc())
        .all()
    )
    
    items = [
        PortfolioImageResponse(
            id=img.id,
            user_id=img.user_id,
            kind=img.kind,
            url=img.url,
            width=img.width,
            height=img.height,
            mime_type=img.mime_type,
            created_at=img.created_at.isoformat(),
        )
        for img in images
    ]
    
    return PortfolioListResponse(items=items)


@public_router.get("/{slug}/wannado", response_model=PortfolioListResponse)
def get_public_artist_wannado(
    slug: str = Path(..., description="Artist slug"),
    db: Session = Depends(get_db),
):
    """Get public 'wanna do' items for an artist by slug."""
    artist = (
        db.query(Artist)
        .join(User, Artist.user_id == User.id)
        .filter(
            or_(Artist.slug == slug, User.username == slug),
            User.account_type == AccountType.ARTIST,
            User.onboarding_completed == True,
        )
        .first()
    )
    
    if not artist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Artist not found",
        )
    
    images = (
        db.query(PortfolioImage)
        .filter(
            PortfolioImage.user_id == artist.user_id,
            PortfolioImage.kind == "wannado",
        )
        .order_by(PortfolioImage.created_at.desc())
        .all()
    )
    
    items = [
        PortfolioImageResponse(
            id=img.id,
            user_id=img.user_id,
            kind=img.kind,
            url=img.url,
            width=img.width,
            height=img.height,
            mime_type=img.mime_type,
            created_at=img.created_at.isoformat(),
        )
        for img in images
    ]
    
    return PortfolioListResponse(items=items)

