"""Add setup_time and game_elements fields

Revision ID: b9e69a1c3e35
Revises: 347f15356ac2
Create Date: 2025-07-04 16:41:47.756630

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b9e69a1c3e35"
down_revision: Union[str, Sequence[str], None] = "347f15356ac2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add new columns
    op.add_column(
        "games", sa.Column("game_elements", sa.VARCHAR(length=500), nullable=True)
    )
    op.add_column(
        "games", sa.Column("setup_time", sa.VARCHAR(length=100), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Remove new columns
    op.drop_column("games", "game_elements")
    op.drop_column("games", "setup_time")
