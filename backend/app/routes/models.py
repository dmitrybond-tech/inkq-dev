"""Model profile and public model routes."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.models.model import Model
from app.models.model_gallery_item import ModelGalleryItem as ModelGalleryItemModel
from app.models.portfolio import PortfolioImage
from app.models.session import Session as SessionModel
from app.models.user import AccountType, User
from app.routes.auth import get_current_session
from app.schemas.model import (
    ModelGalleryItem,
    ModelGalleryListResponse,
    ModelMeResponse,
    ModelUpdateRequest,
    PublicModelCard,
    PublicModelListResponse,
    PublicModelResponse,
)

router = APIRouter(prefix="/models", tags=["models"])
public_router = APIRouter(prefix="/public/models", tags=["public_models"])


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


def get_or_create_model(user: User, db: Session) -> Model:
    """Get the Model record for a user, creating it if missing."""
    model = db.query(Model).filter(Model.user_id == user.id).first()
    if model is None:
        model = Model(user_id=user.id, slug=user.username)
        db.add(model)
        db.commit()
        db.refresh(model)
    # Ensure slug exists for public pages
    if not model.slug:
        model.slug = user.username
        db.add(model)
        db.commit()
        db.refresh(model)
    # Ensure styles is always a list
    if model.styles is None:
        model.styles = []
    return model


def build_model_me_response(user: User, model: Model) -> ModelMeResponse:
    """Build ModelMeResponse from user and model."""
    return ModelMeResponse(
        username=user.username,
        avatar_url=user.avatar_url,
        banner_url=user.banner_url,
        onboarding_completed=user.onboarding_completed,
        display_name=model.display_name,
        about=model.about,
        city=model.city,
        instagram=model.instagram,
        telegram=model.telegram,
    )


@router.get("/me", response_model=ModelMeResponse)
def get_me(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get current authenticated model profile."""
    if user.account_type != AccountType.MODEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only models can access this endpoint",
        )

    model = get_or_create_model(user, db)
    return build_model_me_response(user, model)


@router.put("/me", response_model=ModelMeResponse)
def update_me(
    payload: ModelUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update current authenticated model profile and onboarding flag."""
    if user.account_type != AccountType.MODEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only models can access this endpoint",
        )

    model = get_or_create_model(user, db)
    data = payload.model_dump(exclude_unset=True)

    onboarding_completed = data.pop("onboarding_completed", None)
    if onboarding_completed is not None:
        user.onboarding_completed = bool(onboarding_completed)

    for field, value in data.items():
        setattr(model, field, value)

    db.add(user)
    db.add(model)
    db.commit()
    db.refresh(user)
    db.refresh(model)

    return build_model_me_response(user, model)


def _build_gallery_items_for_model(model: Model, db: Session) -> List[ModelGalleryItem]:
    """Build gallery DTOs for a model from ModelGalleryItem + PortfolioImage."""
    rows: List[ModelGalleryItemModel] = (
        db.query(ModelGalleryItemModel)
        .filter(ModelGalleryItemModel.model_id == model.id)
        .order_by(ModelGalleryItemModel.created_at.desc())
        .all()
    )
    image_ids = [row.image_id for row in rows]
    images_by_id = {}
    if image_ids:
        image_rows: List[PortfolioImage] = (
            db.query(PortfolioImage)
            .filter(PortfolioImage.id.in_(image_ids))
            .all()
        )
        images_by_id = {img.id: img for img in image_rows}

    items: List[ModelGalleryItem] = []
    for row in rows:
        image = images_by_id.get(row.image_id)
        if not image:
            continue
        items.append(
            ModelGalleryItem(
                id=row.id,
                image_url=image.url,
                caption=row.caption,
                created_at=row.created_at,
            )
        )
    return items


@router.get("/me/gallery", response_model=ModelGalleryListResponse)
def list_my_gallery(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List gallery items for current model."""
    if user.account_type != AccountType.MODEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only models can access this endpoint",
        )
    model = get_or_create_model(user, db)
    items = _build_gallery_items_for_model(model, db)
    return ModelGalleryListResponse(items=items)


@public_router.get("/{slug}", response_model=PublicModelResponse)
def get_public_model(
    slug: str = Path(..., description="Model slug"),
    db: Session = Depends(get_db),
):
    """Get public model profile by slug.
    
    Only returns models who have completed onboarding.
    """
    # Try to find by slug first, then fallback to username for backward compatibility
    model = (
        db.query(Model)
        .join(User, Model.user_id == User.id)
        .filter(
            or_(Model.slug == slug, User.username == slug),
            User.account_type == AccountType.MODEL,
            User.onboarding_completed == True,
        )
        .first()
    )
    
    if not model:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    user = db.query(User).filter(User.id == model.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )
    
    # Ensure slug is set
    if not model.slug:
        model.slug = user.username
        db.add(model)
        db.commit()
        db.refresh(model)

    gallery_items = _build_gallery_items_for_model(model, db)

    return PublicModelResponse(
        username=user.username,
        display_name=model.display_name,
        city=model.city,
        about=model.about,
        instagram=model.instagram,
        telegram=model.telegram,
        avatar_url=user.avatar_url,
        banner_url=user.banner_url,
        gallery=gallery_items,
    )


@public_router.get("", response_model=PublicModelListResponse)
def list_public_models(
    db: Session = Depends(get_db),
    city: Optional[str] = Query(default=None, description="Filter by city (case-insensitive)"),
    limit: int = Query(default=16, ge=1, le=48),
    offset: int = Query(default=0, ge=0),
) -> PublicModelListResponse:
    """List public models with optional city filter.

    Only returns models whose associated user has completed onboarding.
    """
    base_query = (
        db.query(User, Model)
        .join(Model, Model.user_id == User.id)
        .filter(
            User.account_type == AccountType.MODEL,
            User.onboarding_completed == True,  # noqa: E712
        )
    )

    if city:
        city_normalized = city.strip().lower()
        if city_normalized:
            base_query = base_query.filter(func.lower(Model.city) == city_normalized)

    total = base_query.count()

    rows = (
        base_query.order_by(Model.created_at.desc())
        .limit(limit)
        .offset(offset)
        .all()
    )

    items: List[PublicModelCard] = []
    for user, model in rows:
        slug = model.slug or user.username
        if not model.slug:
            model.slug = user.username
            db.add(model)
        items.append(
            PublicModelCard(
                id=model.id,
                username=user.username,
                slug=slug,
                display_name=model.display_name,
                city=model.city,
                styles=list(model.styles or []),
                avatar_url=user.avatar_url,
                banner_url=user.banner_url,
            )
        )

    db.commit()

    return PublicModelListResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


