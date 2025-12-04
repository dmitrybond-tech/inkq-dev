"""add_styles_to_models

Revision ID: 219d449bb81c
Revises: b7c9d1e2f3a4
Create Date: 2025-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "219d449bb81c"
down_revision: Union[str, None] = "b7c9d1e2f3a4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add styles JSONB column to models table."""
    op.add_column(
        "models",
        sa.Column(
            "styles",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
            server_default="[]",
        ),
    )


def downgrade() -> None:
    """Drop styles column from models table."""
    op.drop_column("models", "styles")

