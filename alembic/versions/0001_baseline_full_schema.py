"""Baseline: apply full schema SQL.

Revision ID: 0001_baseline_full_schema
Revises:
Create Date: 2026-02-25
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence, Union

import sqlparse
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001_baseline_full_schema"
down_revision: Union[str, None] = None
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
    _execute_sql_file(root / "db" / "full_schema.sql")


def downgrade() -> None:
    raise NotImplementedError("Baseline downgrade is not supported")
