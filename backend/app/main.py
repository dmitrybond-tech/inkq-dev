"""FastAPI application entry point."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from app.routes import auth, users, media, artists, studios, models
from app.config import settings

app = FastAPI(
    title="InkQ API",
    description="InkQ backend API",
    version="1.0.0",
)

# CORS configuration for frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:4321",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(users.router, prefix=settings.api_v1_prefix)
app.include_router(media.router, prefix=settings.api_v1_prefix)
app.include_router(artists.router, prefix=settings.api_v1_prefix)
app.include_router(artists.public_router, prefix=settings.api_v1_prefix)
app.include_router(studios.router, prefix=settings.api_v1_prefix)
app.include_router(studios.public_router, prefix=settings.api_v1_prefix)
app.include_router(models.router, prefix=settings.api_v1_prefix)
app.include_router(models.public_router, prefix=settings.api_v1_prefix)

# Serve media files
media_root = Path(settings.media_root)
media_root.mkdir(parents=True, exist_ok=True)
app.mount(settings.media_url_prefix, StaticFiles(directory=str(media_root)), name="media")


@app.get("/")
def root():
    """Root endpoint."""
    return {"message": "InkQ API", "version": "1.0.0"}


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}

