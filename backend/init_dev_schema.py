"""One-time helper to initialize the dev database schema from SQLAlchemy models.

This is useful if Alembic's migration history says you're at the latest
revision, but the actual database is empty (only `alembic_version` exists).

Usage (from backend directory):

    python init_dev_schema.py

It will create all tables defined on `Base.metadata` (users, artists, studios,
models, sessions, portfolio_images, etc.) in the database pointed to by
INKQ_PG_URL.
"""

from app.db.base import Base, engine

# Import models so they are registered with Base.metadata
from app.models import (  # noqa: F401
    Artist,
    ArtistStudioResident,
    BookingRequest,
    Model,
    PortfolioImage,
    Session,
    Studio,
    User,
)


def main() -> None:
    print("Initializing dev schema using:", engine.url)
    Base.metadata.create_all(bind=engine)
    print("Schema initialization complete.")


if __name__ == "__main__":
    main()


