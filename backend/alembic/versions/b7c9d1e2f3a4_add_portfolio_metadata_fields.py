"""add_portfolio_metadata_fields

Revision ID: b7c9d1e2f3a4
Revises: a1b2c3d4e5f6
Create Date: 2025-12-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b7c9d1e2f3a4"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add optional metadata fields to portfolio_images."""
    op.add_column(
        "portfolio_images",
        sa.Column("title", sa.String(), nullable=True),
    )
    op.add_column(
        "portfolio_images",
        sa.Column("description", sa.String(), nullable=True),
    )
    op.add_column(
        "portfolio_images",
        sa.Column("approx_price", sa.String(), nullable=True),
    )
    op.add_column(
        "portfolio_images",
        sa.Column("placement", sa.String(), nullable=True),
    )


def downgrade() -> None:
    """Drop optional metadata fields from portfolio_images."""
    op.drop_column("portfolio_images", "placement")
    op.drop_column("portfolio_images", "approx_price")
    op.drop_column("portfolio_images", "description")
    op.drop_column("portfolio_images", "title")


