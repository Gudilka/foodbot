"""Seed reference data.

Revision ID: 0002_seed_reference_data
Revises: 0001_baseline_full_schema
Create Date: 2026-02-25
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

import sqlparse
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0002_seed_reference_data"
down_revision: Union[str, None] = "0001_baseline_full_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _execute_sql_file(sql_path: Path) -> None:
    bind = op.get_bind()
    sql = sql_path.read_text(encoding="utf-8")
    sql = sql.replace("BEGIN;\n", "").replace("\nCOMMIT;", "")
    statements = [stmt.strip() for stmt in sqlparse.split(sql) if stmt.strip()]
    for stmt in statements:
        bind.exec_driver_sql(stmt)


def upgrade() -> None:
    root = Path(__file__).resolve().parents[2]
    _execute_sql_file(root / "db" / "seed_reference_data.sql")


def downgrade() -> None:
    # Reference rows can be retained safely.
    return
