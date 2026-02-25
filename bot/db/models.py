from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    telegram_user_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(Text)
    first_name: Mapped[str | None] = mapped_column(Text)
    last_name: Mapped[str | None] = mapped_column(Text)
    language_code: Mapped[str] = mapped_column(Text, nullable=False, default="ru")
    timezone: Mapped[str] = mapped_column(Text, nullable=False, default="Europe/Moscow")
    is_bot_blocked: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    currency: Mapped[str] = mapped_column(Text, nullable=False, default="RUB")
    household_size: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    weekly_budget_rub: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    diet_type: Mapped[str | None] = mapped_column(Text)
    nutrition_goal: Mapped[str | None] = mapped_column(Text)
    monthly_budget_rub: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cooking_skill: Mapped[int | None] = mapped_column(SmallInteger)
    max_cook_time_min: Mapped[int | None] = mapped_column(Integer)
    goal_kcal: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    goal_protein_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    goal_fat_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    goal_carb_g: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    exclude_fast_food: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class DietaryRestriction(Base):
    __tablename__ = "dietary_restrictions"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class UserDietaryRestriction(Base):
    __tablename__ = "user_dietary_restrictions"
    __table_args__ = (UniqueConstraint("user_id", "restriction_id"),)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    restriction_id: Mapped[int] = mapped_column(
        SmallInteger, ForeignKey("dietary_restrictions.id", ondelete="RESTRICT"), primary_key=True
    )
    severity: Mapped[int | None] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Cuisine(Base):
    __tablename__ = "cuisines"

    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)


class UserCuisinePreference(Base):
    __tablename__ = "user_cuisine_preferences"
    __table_args__ = (UniqueConstraint("user_id", "cuisine_id"),)

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    cuisine_id: Mapped[int] = mapped_column(SmallInteger, ForeignKey("cuisines.id", ondelete="CASCADE"), primary_key=True)
    priority: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class UserNotificationSettings(Base):
    __tablename__ = "user_notification_settings"

    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    telegram_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    push_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    email_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sunday_plan_reminder_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    reminder_hour_local: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=18)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class EventLog(Base):
    __tablename__ = "event_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    event_name: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(Text, nullable=False, default="system")
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
    payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)


class BotFSMState(Base):
    __tablename__ = "bot_fsm_states"
    __table_args__ = (UniqueConstraint("bot_id", "chat_id", "user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    bot_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chat_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    state: Mapped[str | None] = mapped_column(Text)
    data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
