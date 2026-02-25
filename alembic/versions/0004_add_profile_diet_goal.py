"""Add diet_type and nutrition_goal to user_profiles.

Revision ID: 0004_add_profile_diet_goal
Revises: 0003_create_bot_fsm_states
Create Date: 2026-02-25
"""

from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0004_add_profile_diet_goal"
down_revision: Union[str, None] = "0003_create_bot_fsm_states"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("user_profiles", sa.Column("diet_type", sa.Text(), nullable=True))
    op.add_column("user_profiles", sa.Column("nutrition_goal", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("user_profiles", "nutrition_goal")
    op.drop_column("user_profiles", "diet_type")
