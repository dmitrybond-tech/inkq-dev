"""Media upload routes for avatars, banners, and portfolio."""
import io
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form, Path
from sqlalchemy.orm import Session
from PIL import Image
from app.db.base import get_db
from app.models.user import User, AccountType
from app.models.session import Session as SessionModel
from app.models.portfolio import PortfolioImage
from app.models.model import Model
from app.models.model_gallery_item import ModelGalleryItem
from app.routes.auth import get_current_session
from app.utils.media import (
    validate_file,
    get_avatars_dir,
    get_banners_dir,
    get_portfolio_dir,
    generate_safe_filename,
    process_avatar,
    process_banner,
    process_portfolio,
    save_image,
    get_media_url,
    MAX_UPLOAD_SIZE,
)
from app.schemas.media import (
    MediaUploadResponse,
    PortfolioImageResponse,
    PortfolioImageUpdateRequest,
    PortfolioListResponse,
    PortfolioUploadResponse,
)
from app.schemas.model import ModelGalleryItem as ModelGalleryItemSchema, ModelGalleryListResponse

router = APIRouter(prefix="/media", tags=["media"])


def get_current_user(
    session: SessionModel = Depends(get_current_session),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user."""
    user = db.query(User).filter(User.id == session.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


def get_role_endpoint_prefix(account_type: AccountType) -> str:
    """Get the role-specific endpoint prefix."""
    if account_type == AccountType.ARTIST:
        return "artists"
    elif account_type == AccountType.STUDIO:
        return "studios"
    elif account_type == AccountType.MODEL:
        return "models"
    else:
        raise ValueError(f"Invalid account_type: {account_type}")


# Avatar upload endpoints
@router.post("/artists/me/avatar", response_model=MediaUploadResponse, status_code=status.HTTP_200_OK)
async def upload_artist_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload avatar for artist."""
    if user.account_type != AccountType.ARTIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only artists can upload to this endpoint"
        )
    return await _upload_avatar(file, user, db)


@router.post("/studios/me/avatar", response_model=MediaUploadResponse, status_code=status.HTTP_200_OK)
async def upload_studio_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload avatar for studio."""
    if user.account_type != AccountType.STUDIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studios can upload to this endpoint"
        )
    return await _upload_avatar(file, user, db)


@router.post("/models/me/avatar", response_model=MediaUploadResponse, status_code=status.HTTP_200_OK)
async def upload_model_avatar(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload avatar for model."""
    if user.account_type != AccountType.MODEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only models can upload to this endpoint"
        )
    return await _upload_avatar(file, user, db)


async def _upload_avatar(file: UploadFile, user: User, db: Session) -> MediaUploadResponse:
    """Shared logic for avatar upload."""
    # Validate file type
    validate_file(file)
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / (1024 * 1024)} MB"
        )
    
    # Load and process image
    try:
        image = Image.open(io.BytesIO(content))
        processed_image, width, height = process_avatar(image)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )
    
    # Generate filename and save
    filename = generate_safe_filename(user.id, "avatar", "webp")
    file_path = get_avatars_dir() / filename
    save_image(processed_image, file_path, format="WEBP")
    
    # Update user record
    media_url = get_media_url(file_path)
    user.avatar_url = media_url
    db.add(user)
    db.commit()
    db.refresh(user)

    return MediaUploadResponse(url=media_url, width=width, height=height)


# Banner upload endpoints
@router.post("/artists/me/banner", response_model=MediaUploadResponse, status_code=status.HTTP_200_OK)
async def upload_artist_banner(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload banner for artist."""
    if user.account_type != AccountType.ARTIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only artists can upload to this endpoint"
        )
    return await _upload_banner(file, user, db)


@router.post("/studios/me/banner", response_model=MediaUploadResponse, status_code=status.HTTP_200_OK)
async def upload_studio_banner(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload banner for studio."""
    if user.account_type != AccountType.STUDIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studios can upload to this endpoint"
        )
    return await _upload_banner(file, user, db)


@router.post("/models/me/banner", response_model=MediaUploadResponse, status_code=status.HTTP_200_OK)
async def upload_model_banner(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload banner for model."""
    if user.account_type != AccountType.MODEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only models can upload to this endpoint"
        )
    return await _upload_banner(file, user, db)


async def _upload_banner(file: UploadFile, user: User, db: Session) -> MediaUploadResponse:
    """Shared logic for banner upload."""
    # Validate file type
    validate_file(file)
    
    # Read file content
    content = await file.read()
    
    # Check file size
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum size: {MAX_UPLOAD_SIZE / (1024 * 1024)} MB"
        )
    
    # Load and process image
    try:
        image = Image.open(io.BytesIO(content))
        processed_image, width, height = process_banner(image)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image file: {str(e)}"
        )
    
    # Generate filename and save
    filename = generate_safe_filename(user.id, "banner", "webp")
    file_path = get_banners_dir() / filename
    save_image(processed_image, file_path, format="WEBP")
    
    # Update user record
    media_url = get_media_url(file_path)
    user.banner_url = media_url
    db.add(user)
    db.commit()
    db.refresh(user)

    return MediaUploadResponse(url=media_url, width=width, height=height)


# Portfolio upload endpoints
@router.post("/artists/me/portfolio", response_model=PortfolioUploadResponse, status_code=status.HTTP_200_OK)
async def upload_artist_portfolio(
    files: List[UploadFile] = File(...),
    kind: str = Form("portfolio"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload portfolio images for artist."""
    if user.account_type != AccountType.ARTIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only artists can upload to this endpoint"
        )
    return await _upload_portfolio(files, kind, user, db)


@router.post("/studios/me/portfolio", response_model=PortfolioUploadResponse, status_code=status.HTTP_200_OK)
async def upload_studio_portfolio(
    files: List[UploadFile] = File(...),
    kind: str = Form("portfolio"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload portfolio images for studio."""
    if user.account_type != AccountType.STUDIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studios can upload to this endpoint"
        )
    return await _upload_portfolio(files, kind, user, db)


@router.post("/models/me/portfolio", response_model=PortfolioUploadResponse, status_code=status.HTTP_200_OK)
async def upload_model_portfolio(
    files: List[UploadFile] = File(...),
    kind: str = Form("portfolio"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload portfolio images for model."""
    if user.account_type != AccountType.MODEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only models can upload to this endpoint"
        )
    return await _upload_portfolio(files, kind, user, db)


async def _upload_portfolio(
    files: List[UploadFile],
    kind: str,
    user: User,
    db: Session
) -> PortfolioUploadResponse:
    """Shared logic for portfolio upload."""
    if kind not in ("portfolio", "wannado"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="kind must be 'portfolio' or 'wannado'"
        )
    
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required"
        )
    
    created_items = []
    portfolio_dir = get_portfolio_dir(user.id)
    
    for file in files:
        # Validate file type
        validate_file(file)
        
        # Read file content
        content = await file.read()
        
        # Check file size
        if len(content) > MAX_UPLOAD_SIZE:
            continue  # Skip oversized files, but continue with others
        
        # Load and process image
        try:
            image = Image.open(io.BytesIO(content))
            processed_image, width, height = process_portfolio(image)
            mime_type = file.content_type or "image/webp"
        except Exception:
            continue  # Skip invalid images
        
        # Generate filename and save
        filename = generate_safe_filename(user.id, "portfolio", "webp")
        file_path = portfolio_dir / filename
        save_image(processed_image, file_path, format="WEBP")
        
        # Create database record
        media_url = get_media_url(file_path)
        portfolio_image = PortfolioImage(
            user_id=user.id,
            kind=kind,
            url=media_url,
            width=width,
            height=height,
            mime_type=mime_type
        )
        db.add(portfolio_image)
        db.flush()
        
        created_items.append(
            PortfolioImageResponse(
                id=portfolio_image.id,
                user_id=portfolio_image.user_id,
                kind=portfolio_image.kind,
                url=portfolio_image.url,
                width=portfolio_image.width,
                height=portfolio_image.height,
                mime_type=portfolio_image.mime_type,
                created_at=portfolio_image.created_at.isoformat(),
                title=portfolio_image.title,
                description=portfolio_image.description,
                approx_price=portfolio_image.approx_price,
                placement=portfolio_image.placement,
            )
        )
    
    db.commit()
    
    return PortfolioUploadResponse(items=created_items)


# Portfolio list endpoints
@router.get("/artists/me/portfolio", response_model=PortfolioListResponse)
async def list_artist_portfolio(
    kind: Optional[str] = Query(
        default=None,
        description="Optional kind filter: 'portfolio' or 'wannado'",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List portfolio images for artist."""
    if user.account_type != AccountType.ARTIST:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only artists can access this endpoint"
        )
    return await _list_portfolio(user, db, kind=kind)


@router.get("/studios/me/portfolio", response_model=PortfolioListResponse)
async def list_studio_portfolio(
    kind: Optional[str] = Query(
        default=None,
        description="Optional kind filter: 'portfolio' or 'wannado'",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List portfolio images for studio."""
    if user.account_type != AccountType.STUDIO:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only studios can access this endpoint"
        )
    return await _list_portfolio(user, db, kind=kind)


@router.get("/models/me/portfolio", response_model=PortfolioListResponse)
async def list_model_portfolio(
    kind: Optional[str] = Query(
        default=None,
        description="Optional kind filter: 'portfolio' or 'wannado'",
    ),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List portfolio images for model."""
    if user.account_type != AccountType.MODEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only models can access this endpoint"
        )
    return await _list_portfolio(user, db, kind=kind)


async def _list_portfolio(user: User, db: Session, kind: Optional[str] = None) -> PortfolioListResponse:
    """Shared logic for portfolio list.

    If kind is provided and valid ('portfolio' or 'wannado'), results are filtered by kind.
    Otherwise, all portfolio images for the user are returned.
    """
    query = db.query(PortfolioImage).filter(PortfolioImage.user_id == user.id)

    if kind in ("portfolio", "wannado"):
        query = query.filter(PortfolioImage.kind == kind)

    images = query.all()
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
            title=img.title,
            description=img.description,
            approx_price=img.approx_price,
            placement=img.placement,
        )
        for img in images
    ]
    return PortfolioListResponse(items=items)


# Portfolio delete endpoint
@router.delete("/portfolio/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio_image(
    image_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a portfolio image. Only the owner can delete."""
    portfolio_image = db.query(PortfolioImage).filter(PortfolioImage.id == image_id).first()
    
    if not portfolio_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio image not found"
        )
    
    if portfolio_image.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own portfolio images"
        )
    
    # TODO: Optionally delete the file from disk
    # For now, we just delete the DB record
    
    db.delete(portfolio_image)
    db.commit()
    return None


@router.patch("/portfolio/{image_id}", response_model=PortfolioImageResponse)
async def update_portfolio_image_metadata(
    image_id: int,
    payload: PortfolioImageUpdateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update metadata for a portfolio image owned by the current user.

    Only the owner can update; partial updates are supported.
    """
    portfolio_image = (
        db.query(PortfolioImage)
        .filter(
            PortfolioImage.id == image_id,
            PortfolioImage.user_id == user.id,
        )
        .first()
    )

    if not portfolio_image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio image not found",
        )

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(portfolio_image, field, value)

    db.add(portfolio_image)
    db.commit()
    db.refresh(portfolio_image)

    return PortfolioImageResponse(
        id=portfolio_image.id,
        user_id=portfolio_image.user_id,
        kind=portfolio_image.kind,
        url=portfolio_image.url,
        width=portfolio_image.width,
        height=portfolio_image.height,
        mime_type=portfolio_image.mime_type,
        created_at=portfolio_image.created_at.isoformat(),
        title=portfolio_image.title,
        description=portfolio_image.description,
        approx_price=portfolio_image.approx_price,
        placement=portfolio_image.placement,
    )


# Model gallery endpoints (separate from raw portfolio list)
@router.post(
    "/models/me/gallery",
    response_model=ModelGalleryListResponse,
    status_code=status.HTTP_200_OK,
)
async def upload_model_gallery(
    files: List[UploadFile] = File(...),
    caption: Optional[str] = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Upload gallery images for model and create ModelGalleryItem records."""
    if user.account_type != AccountType.MODEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only models can upload to this endpoint",
        )

    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one file is required",
        )

    # Ensure model record exists
    model = db.query(Model).filter(Model.user_id == user.id).first()
    if model is None:
        model = Model(user_id=user.id, slug=user.username)
        db.add(model)
        db.commit()
        db.refresh(model)

    created_items: List[ModelGalleryItemSchema] = []
    portfolio_dir = get_portfolio_dir(user.id)

    for file in files:
        validate_file(file)
        content = await file.read()
        if len(content) > MAX_UPLOAD_SIZE:
            # Skip oversized files but continue with others
            continue

        try:
            image = Image.open(io.BytesIO(content))
            processed_image, width, height = process_portfolio(image)
            mime_type = file.content_type or "image/webp"
        except Exception:
            # Skip invalid images
            continue

        filename = generate_safe_filename(user.id, "portfolio", "webp")
        file_path = portfolio_dir / filename
        save_image(processed_image, file_path, format="WEBP")

        media_url = get_media_url(file_path)
        portfolio_image = PortfolioImage(
            user_id=user.id,
            kind="portfolio",
            url=media_url,
            width=width,
            height=height,
            mime_type=mime_type,
        )
        db.add(portfolio_image)
        db.flush()

        gallery_item = ModelGalleryItem(
            model_id=model.id,
            image_id=portfolio_image.id,
            caption=caption,
        )
        db.add(gallery_item)
        db.flush()

        created_items.append(
            ModelGalleryItemSchema(
                id=gallery_item.id,
                image_url=portfolio_image.url,
                caption=gallery_item.caption,
                created_at=gallery_item.created_at,
            )
        )

    db.commit()

    return ModelGalleryListResponse(items=created_items)


@router.get(
    "/models/me/gallery",
    response_model=ModelGalleryListResponse,
)
async def list_model_gallery(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List gallery items for current model."""
    if user.account_type != AccountType.MODEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only models can access this endpoint",
        )

    model = db.query(Model).filter(Model.user_id == user.id).first()
    if model is None:
        model = Model(user_id=user.id, slug=user.username)
        db.add(model)
        db.commit()
        db.refresh(model)

    items: List[ModelGalleryItem] = (
        db.query(ModelGalleryItem)
        .filter(ModelGalleryItem.model_id == model.id)
        .order_by(ModelGalleryItem.created_at.desc())
        .all()
    )
    image_ids = [item.image_id for item in items]
    images_by_id = {}
    if image_ids:
        image_rows: List[PortfolioImage] = (
            db.query(PortfolioImage)
            .filter(PortfolioImage.id.in_(image_ids))
            .all()
        )
        images_by_id = {img.id: img for img in image_rows}

    dto_items: List[ModelGalleryItemSchema] = []
    for item in items:
        image = images_by_id.get(item.image_id)
        if not image:
            continue
        dto_items.append(
            ModelGalleryItemSchema(
                id=item.id,
                image_url=image.url,
                caption=item.caption,
                created_at=item.created_at,
            )
        )

    return ModelGalleryListResponse(items=dto_items)


@router.delete(
    "/models/me/gallery/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_model_gallery_item(
    item_id: int = Path(..., description="Gallery item id"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a gallery item owned by the current model."""
    if user.account_type != AccountType.MODEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only models can access this endpoint",
        )

    model = db.query(Model).filter(Model.user_id == user.id).first()
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )

    item = (
        db.query(ModelGalleryItem)
        .filter(
            ModelGalleryItem.id == item_id,
            ModelGalleryItem.model_id == model.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery item not found",
        )

    db.delete(item)
    db.commit()
    return None


@router.patch(
    "/models/me/gallery/{item_id}",
    response_model=ModelGalleryItemSchema,
)
async def update_model_gallery_item_caption(
    item_id: int,
    caption: Optional[str] = Form(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update caption for a model gallery item owned by the current model."""
    if user.account_type != AccountType.MODEL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only models can access this endpoint",
        )

    model = db.query(Model).filter(Model.user_id == user.id).first()
    if model is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Model not found",
        )

    item = (
        db.query(ModelGalleryItem)
        .filter(
            ModelGalleryItem.id == item_id,
            ModelGalleryItem.model_id == model.id,
        )
        .first()
    )
    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Gallery item not found",
        )

    item.caption = caption
    db.add(item)
    db.commit()
    db.refresh(item)

    image = db.query(PortfolioImage).filter(PortfolioImage.id == item.image_id).first()
    if not image:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        )

    return ModelGalleryItemSchema(
        id=item.id,
        image_url=image.url,
        caption=item.caption,
        created_at=item.created_at,
    )

