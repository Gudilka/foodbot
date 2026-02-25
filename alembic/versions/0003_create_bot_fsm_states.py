"""Create bot_fsm_states table for aiogram Postgres storage.

Revision ID: 0003_create_bot_fsm_states
Revises: 0002_seed_reference_data
Create Date: 2026-02-25
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "0003_create_bot_fsm_states"
down_revision: Union[str, None] = "0002_seed_reference_data"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "bot_fsm_states",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("bot_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("state", sa.Text(), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bot_id", "chat_id", "user_id", name="uq_bot_fsm_states_key"),
    )
    op.create_index("idx_bot_fsm_states_updated_at", "bot_fsm_states", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_bot_fsm_states_updated_at", table_name="bot_fsm_states")
    op.drop_table("bot_fsm_states")
