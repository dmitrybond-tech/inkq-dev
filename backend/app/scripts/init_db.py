"""Database initialization script for InkQ backend.

This script is the single entrypoint for initializing/updating the database
schema for local development. It uses the same SQLAlchemy engine and settings
as the FastAPI app and can optionally integrate with Alembic migrations.

The script is **idempotent** and safe to run multiple times. It supports:

- Creating all tables defined in the SQLAlchemy models (non-destructive)
- Optionally dropping and recreating all tables (destructive, opt-in)
- Optional Alembic migrations and version stamping
- A placeholder seeding hook for future reference data
- Optional SQL echo for debugging

Usage examples (from `backend` directory, after activating the venv):

    cd C:\\PersonalProjects\\Inkq_v1.0\\backend
    .\\.venv\\Scripts\\activate

    # Create all tables (non-destructive, no Alembic)
    python .\\app\\scripts\\init_db.py

    # Drop and recreate all tables from models only
    python .\\app\\scripts\\init_db.py --drop-all

    # Drop, recreate and (placeholder) seed base data
    python .\\app\\scripts\\init_db.py --drop-all --seed

    # Use Alembic migrations (upgrade head) plus model-based create_all
    python .\\app\\scripts\\init_db.py --use-alembic

    # Verbose SQL logging
    python .\\app\\scripts\\init_db.py --echo-sql
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Add backend directory to path for imports (when run as a script)
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session
from alembic import command
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory

from app.db.base import Base, SessionLocal, engine
from app.config import settings

# Import all models so they are registered with Base.metadata
from app.models import (  # noqa: F401
    Artist,
    ArtistStudioResident,
    BookingRequest,
    Model,
    ModelGalleryItem,
    PortfolioImage,
    Session as DbSession,
    Studio,
    User,
)


logger = logging.getLogger(__name__)


def configure_logging() -> None:
    """Configure root logging for the script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )


def get_alembic_config() -> Config:
    """Get Alembic configuration object."""
    alembic_ini_path = backend_dir / "alembic.ini"
    alembic_cfg = Config(str(alembic_ini_path))
    # Override sqlalchemy.url with our settings
    alembic_cfg.set_main_option("sqlalchemy.url", settings.inkq_pg_url)
    return alembic_cfg


def get_current_db_revision() -> Optional[str]:
    """Get the current Alembic revision from the database, if any."""
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()
            return current_rev
    except Exception:
        # alembic_version table might not exist or DB might be empty
        return None


def get_head_revision() -> Optional[str]:
    """Get the head revision from Alembic script directory, if configured."""
    try:
        alembic_cfg = get_alembic_config()
        script = ScriptDirectory.from_config(alembic_cfg)
        head = script.get_current_head()
        return head
    except Exception:
        # No migrations or Alembic not properly configured
        return None


def drop_all_tables() -> None:
    """Drop all application tables (destructive).

    This relies on SQLAlchemy metadata and uses the shared engine.
    """
    logger.info("Dropping all tables from SQLAlchemy metadata...")
    Base.metadata.drop_all(bind=engine)
    logger.info("All tables dropped successfully.")


def create_all_tables() -> None:
    """Create all tables defined in SQLAlchemy models (idempotent)."""
    logger.info("Creating all tables from SQLAlchemy models (if missing)...")
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    tables = inspector.get_table_names()
    app_tables = [t for t in tables if t != "alembic_version"]
    app_tables_sorted = ", ".join(sorted(app_tables)) if app_tables else "<none>"
    logger.info(
        "Verified application tables (%d): %s",
        len(app_tables),
        app_tables_sorted,
    )


def ensure_artist_slug_column() -> None:
    """Ensure the `slug` column exists on the `artists` table.

    Uses a raw SQL `ALTER TABLE ... ADD COLUMN IF NOT EXISTS` statement so it
    is safe and idempotent to call even if the column already exists.
    """
    logger.info("Ensuring `slug` column exists on `artists` table...")
    ddl = text("ALTER TABLE artists ADD COLUMN IF NOT EXISTS slug VARCHAR(255);")
    with engine.begin() as conn:
        conn.execute(ddl)
    logger.info("Verified `artists.slug` column.")


def run_alembic_upgrade_head() -> None:
    """Run Alembic migrations up to head, if configured."""
    head_rev = get_head_revision()
    if head_rev is None:
        logger.warning(
            "Alembic appears not to be configured (no head revision). "
            "Skipping alembic upgrade."
        )
        return

    current_rev = get_current_db_revision()
    if current_rev == head_rev:
        logger.info("Database is already at Alembic head revision: %s", head_rev)
        return

    logger.info(
        "Running Alembic upgrade to head (current=%s, head=%s)...",
        current_rev,
        head_rev,
    )
    alembic_cfg = get_alembic_config()
    command.upgrade(alembic_cfg, "head")
    logger.info("Alembic migrations applied successfully.")


def stamp_alembic_head_if_available() -> None:
    """Stamp Alembic version table to head, if Alembic is configured."""
    head_rev = get_head_revision()
    if head_rev is None:
        # Nothing to stamp
        return

    logger.info("Stamping Alembic version to head: %s", head_rev)
    alembic_cfg = get_alembic_config()
    command.stamp(alembic_cfg, "head")
    logger.info("Alembic version stamped to head.")


def seed_base_data(db: Session) -> None:
    """Seed base/reference data.

    Creates a demo artist with completed onboarding for testing the catalog.
    The explicit `Session` parameter keeps the seeding logic testable and easy to extend.
    """
    logger.info("Running base data seed...")
    
    from app.models.user import User, AccountType
    from app.models.artist import Artist
    
    # Check if demo artist already exists
    demo_email = "demo-artist@inkq.test"
    existing_user = db.query(User).filter(User.email == demo_email).first()
    if existing_user:
        logger.info("Demo artist already exists, skipping seed.")
        return
    
    # Create demo artist user
    # Use proper bcrypt hashing
    from app.routes.auth import hash_password
    password_hash = hash_password("demo123")
    
    demo_user = User(
        email=demo_email,
        password_hash=password_hash,
        username="demo-artist",
        account_type=AccountType.ARTIST,
        onboarding_completed=True,
    )
    db.add(demo_user)
    db.flush()  # Get the user ID
    
    # Create artist profile
    demo_artist = Artist(
        user_id=demo_user.id,
        display_name="Demo Artist",
        about="A demo artist profile for testing the catalog. Specializes in traditional and blackwork styles.",
        styles=["traditional", "blackwork"],  # JSONB array
        city="Berlin",
        session_price=150,
        instagram="@demo_artist",
        telegram="@demo_artist_tg",
    )
    db.add(demo_artist)
    
    db.commit()
    logger.info("Demo artist created: %s (email: %s)", demo_user.username, demo_email)


def verify_tables() -> None:
    """Log a summary of the existing application tables."""
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    app_tables = [t for t in tables if t != "alembic_version"]
    app_tables_sorted = ", ".join(sorted(app_tables)) if app_tables else "<none>"
    logger.info(
        "Final application tables in database (%d): %s",
        len(app_tables),
        app_tables_sorted,
    )


def init_db(
    drop_all: bool = False,
    seed: bool = False,
    use_alembic: bool = False,
    echo_sql: bool = False,
) -> None:
    """Initialize database schema based on SQLAlchemy models (and optionally Alembic).

    - Optionally drops all tables first (when `drop_all` is True).
    - Optionally runs Alembic migrations (when `use_alembic` is True).
    - Always calls `Base.metadata.create_all` to ensure tables exist.
    - Optionally runs seeding logic (when `seed` is True).
    """
    if echo_sql:
        # Toggle SQL echo on the shared engine for the duration of this script.
        engine.echo = True
        logger.info("SQL echo enabled on engine.")

    logger.info("Initializing database using URL: %s", engine.url)

    if drop_all:
        logger.warning(
            "Requested destructive operation: dropping all tables before recreation."
        )
        drop_all_tables()
    else:
        logger.info("Drop-all not requested; existing tables will be preserved.")

    if use_alembic:
        logger.info("Alembic integration requested; will run migrations.")
        try:
            run_alembic_upgrade_head()
        except Exception as exc:
            logger.warning(
                "Alembic upgrade failed (%s). Continuing with model-based table "
                "creation to ensure schema exists.",
                exc,
            )
    else:
        logger.info("Alembic not requested; skipping migrations.")

    # Ensure all tables from SQLAlchemy models exist.
    create_all_tables()

    # Ensure artist-specific schema tweaks that are not covered by Alembic
    # migrations yet (safe, idempotent ALTER).
    ensure_artist_slug_column()

    # Keep Alembic version in sync when Alembic is configured at all.
    try:
        stamp_alembic_head_if_available()
    except Exception as exc:
        logger.warning(
            "Could not stamp Alembic version to head (%s). "
            "Database tables are created but Alembic metadata may be out of sync.",
            exc,
        )

    # Optional seeding step.
    if seed:
        logger.info("Seeding requested; running `seed_base_data`...")
        db = SessionLocal()
        try:
            seed_base_data(db)
        finally:
            db.close()
        logger.info("Seeding completed.")
    else:
        logger.info("Seeding not requested; skipping base data seed.")

    verify_tables()
    logger.info("Database initialization complete.")


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    """Parse command-line arguments for the init_db CLI."""
    parser = argparse.ArgumentParser(
        description=(
            "Initialize the InkQ Postgres schema for local development. "
            "By default this creates any missing tables using SQLAlchemy models "
            "without dropping existing data."
        )
    )

    parser.add_argument(
        "--drop-all",
        action="store_true",
        help=(
            "Drop ALL tables before recreating them from the SQLAlchemy models. "
            "This is DESTRUCTIVE and intended only for local/dev use."
        ),
    )
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Run base data seeding after tables are created.",
    )
    parser.add_argument(
        "--use-alembic",
        action="store_true",
        help=(
            "Use Alembic migrations (alembic upgrade head) in addition to "
            "SQLAlchemy create_all. Recommended if your DB is tracked via Alembic."
        ),
    )
    parser.add_argument(
        "--echo-sql",
        action="store_true",
        help="Enable SQL echo on the shared SQLAlchemy engine for debugging.",
    )

    return parser.parse_args(argv)


if __name__ == "__main__":
    configure_logging()
    try:
        args = parse_args()
        init_db(
            drop_all=args.drop_all,
            seed=args.seed,
            use_alembic=args.use_alembic,
            echo_sql=args.echo_sql,
        )
    except KeyboardInterrupt:
        logger.error("Initialization cancelled by user (KeyboardInterrupt).")
        sys.exit(1)
    except Exception as exc:
        logger.exception("Initialization failed: %s", exc)
        sys.exit(1)
