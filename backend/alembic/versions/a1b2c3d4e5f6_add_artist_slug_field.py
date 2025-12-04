"""add_artist_slug_field

Revision ID: a1b2c3d4e5f6
Revises: 9b0a1c2d3e45
Create Date: 2025-01-21 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "9b0a1c2d3e45"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add slug column (nullable initially for existing records)
    op.add_column("artists", sa.Column("slug", sa.String(), nullable=True))
    
    # Create unique index
    op.create_index(op.f("ix_artists_slug"), "artists", ["slug"], unique=True)
    
    # Initialize slug from username for existing artists
    # This uses raw SQL since we need to join with users table
    op.execute("""
        UPDATE artists
        SET slug = users.username
        FROM users
        WHERE artists.user_id = users.id
        AND artists.slug IS NULL
    """)


def downgrade() -> None:
    # Drop index and column
    op.drop_index(op.f("ix_artists_slug"), table_name="artists")
    op.drop_column("artists", "slug")

