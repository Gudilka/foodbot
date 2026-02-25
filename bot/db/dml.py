from __future__ import annotations

from sqlalchemy import Table
from sqlalchemy.ext.asyncio import AsyncSession


def upsert_insert(session: AsyncSession, table: Table):
    dialect_name = session.get_bind().dialect.name
    if dialect_name == "sqlite":
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        return sqlite_insert(table)
    if dialect_name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert as postgres_insert

        return postgres_insert(table)
    raise RuntimeError(f"Unsupported SQL dialect for upsert: {dialect_name}")
