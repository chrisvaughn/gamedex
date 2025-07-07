"""Add play_logs table

Revision ID: add_play_logs_table
Revises: b9e69a1c3e35
Create Date: 2025-07-07 06:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "add_play_logs_table"
down_revision: Union[str, Sequence[str], None] = "b9e69a1c3e35"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create play_logs table
    op.create_table(
        "play_logs",
        sa.Column("id", sa.INTEGER(), nullable=False),
        sa.Column("game_id", sa.INTEGER(), nullable=False),
        sa.Column("played_date", sa.DATETIME(), nullable=False),
        sa.Column("players", sa.VARCHAR(length=500), nullable=True),
        sa.Column("notes", sa.VARCHAR(), nullable=True),
        sa.Column("duration_minutes", sa.INTEGER(), nullable=True),
        sa.Column("winner", sa.VARCHAR(length=100), nullable=True),
        sa.Column("created_at", sa.DATETIME(), nullable=True),
        sa.Column("updated_at", sa.DATETIME(), nullable=True),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["games.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_play_logs_id"), "play_logs", ["id"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    # Drop play_logs table
    op.drop_index(op.f("ix_play_logs_id"), table_name="play_logs")
    op.drop_table("play_logs")
