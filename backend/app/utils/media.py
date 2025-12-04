"""Media handling utilities for image processing and storage."""
import os
import secrets
from pathlib import Path
from typing import Tuple, Optional
from PIL import Image
from fastapi import UploadFile, HTTPException, status
from app.config import settings

# Supported image MIME types
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
}

# Max upload size in bytes
MAX_UPLOAD_SIZE = settings.max_upload_size_mb * 1024 * 1024


def get_media_root() -> Path:
    """Get the media root directory, creating it if it doesn't exist."""
    root = Path(settings.media_root)
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_avatars_dir() -> Path:
    """Get the avatars directory."""
    dir_path = get_media_root() / "avatars"
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_banners_dir() -> Path:
    """Get the banners directory."""
    dir_path = get_media_root() / "banners"
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_portfolio_dir(user_id: int) -> Path:
    """Get the portfolio directory for a specific user."""
    dir_path = get_media_root() / "portfolio" / f"user_{user_id}"
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def validate_file(file: UploadFile) -> None:
    """Validate uploaded file type and size."""
    # Check MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}"
        )
    
    # Check file size (we need to read the file to check size)
    # This will be done in the route handler after reading the file


def generate_safe_filename(user_id: int, prefix: str = "", extension: str = "webp") -> str:
    """Generate a safe filename for uploaded media."""
    timestamp = int(secrets.token_hex(4), 16)  # Random 4-byte hex as timestamp-like identifier
    safe_prefix = f"{prefix}_" if prefix else ""
    return f"{safe_prefix}user_{user_id}_{timestamp}.{extension}"


def normalize_image(
    image: Image.Image,
    target_width: int,
    target_height: int,
    crop_mode: str = "center"
) -> Image.Image:
    """
    Normalize an image to target dimensions.
    
    Args:
        image: PIL Image object
        target_width: Target width in pixels
        target_height: Target height in pixels
        crop_mode: "center" (center crop) or "fit" (fit with padding)
    
    Returns:
        Normalized PIL Image
    """
    if crop_mode == "center":
        # Center crop to match aspect ratio, then resize
        current_aspect = image.width / image.height
        target_aspect = target_width / target_height
        
        if current_aspect > target_aspect:
            # Image is wider, crop width
            new_width = int(image.height * target_aspect)
            left = (image.width - new_width) // 2
            image = image.crop((left, 0, left + new_width, image.height))
        else:
            # Image is taller, crop height
            new_height = int(image.width / target_aspect)
            top = (image.height - new_height) // 2
            image = image.crop((0, top, image.width, top + new_height))
        
        # Resize to target dimensions
        image = image.resize((target_width, target_height), Image.Resampling.LANCZOS)
    else:
        # Fit mode: resize maintaining aspect ratio, then pad
        image.thumbnail((target_width, target_height), Image.Resampling.LANCZOS)
        new_image = Image.new("RGB", (target_width, target_height), (255, 255, 255))
        paste_x = (target_width - image.width) // 2
        paste_y = (target_height - image.height) // 2
        new_image.paste(image, (paste_x, paste_y))
        image = new_image
    
    return image


def process_avatar(image: Image.Image) -> Tuple[Image.Image, int, int]:
    """Process image for avatar: normalize to 400x400."""
    normalized = normalize_image(image, 400, 400, crop_mode="center")
    return normalized, 400, 400


def process_banner(image: Image.Image) -> Tuple[Image.Image, int, int]:
    """Process image for banner: normalize to ~1584x396 (4:1 aspect)."""
    normalized = normalize_image(image, 1584, 396, crop_mode="center")
    return normalized, 1584, 396


def process_portfolio(image: Image.Image) -> Tuple[Image.Image, int, int]:
    """
    Process image for portfolio: normalize to 1200x1200 (square) or 1200x627 (wide).
    Chooses based on image orientation.
    """
    aspect = image.width / image.height
    if aspect >= 1.0:
        # Wide or square: use 1200x627
        normalized = normalize_image(image, 1200, 627, crop_mode="center")
        return normalized, 1200, 627
    else:
        # Tall: use 1200x1200 (square)
        normalized = normalize_image(image, 1200, 1200, crop_mode="center")
        return normalized, 1200, 1200


def save_image(image: Image.Image, file_path: Path, format: str = "WEBP", quality: int = 85) -> None:
    """Save PIL Image to file path."""
    # Convert RGBA to RGB if needed (for JPEG compatibility)
    if image.mode == "RGBA" and format == "JPEG":
        rgb_image = Image.new("RGB", image.size, (255, 255, 255))
        rgb_image.paste(image, mask=image.split()[3])  # Use alpha channel as mask
        image = rgb_image
    elif image.mode not in ("RGB", "L"):
        image = image.convert("RGB")
    
    image.save(file_path, format=format, quality=quality, optimize=True)


def get_media_url(file_path: Path) -> str:
    """Convert file path to media URL."""
    # Get relative path from media root
    media_root = get_media_root()
    try:
        relative_path = file_path.relative_to(media_root)
        # Use forward slashes for URLs
        url_path = str(relative_path).replace("\\", "/")
        return f"{settings.media_url_prefix}/{url_path}"
    except ValueError:
        # If path is not under media_root, return as-is
        return str(file_path)

