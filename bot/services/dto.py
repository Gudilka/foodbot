from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator


class RegistrationDraft(BaseModel):
    telegram_user_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    language_code: str = "ru"
    timezone: str = "Europe/Moscow"

    weekly_budget_rub: Decimal = Field(ge=Decimal("500"), le=Decimal("100000"))
    household_size: int = Field(default=1, ge=1, le=10)
    cooking_skill: int = Field(default=3, ge=1, le=5)
    max_cook_time_min: int = Field(default=60, ge=10, le=240)
    goal_kcal: Decimal | None = Field(default=None, ge=Decimal("0"))
    goal_protein_g: Decimal | None = Field(default=None, ge=Decimal("0"))
    goal_fat_g: Decimal | None = Field(default=None, ge=Decimal("0"))
    goal_carb_g: Decimal | None = Field(default=None, ge=Decimal("0"))
    exclude_fast_food: bool = True
    notes: str | None = None

    dietary_restriction_codes: list[str] = Field(default_factory=list)
    cuisine_codes: list[str] = Field(default_factory=list)

    sunday_plan_reminder_enabled: bool = True
    reminder_hour_local: int = Field(default=18, ge=0, le=23)

    @field_validator("notes")
    @classmethod
    def normalize_notes(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        return cleaned or None

    @field_validator("dietary_restriction_codes", "cuisine_codes")
    @classmethod
    def deduplicate_codes(cls, value: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for code in value:
            normalized = code.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                ordered.append(normalized)
        return ordered


class ProfileView(BaseModel):
    telegram_user_id: int
    weekly_budget_rub: Decimal
    household_size: int
    cooking_skill: int | None
    max_cook_time_min: int | None
    goal_kcal: Decimal | None
    goal_protein_g: Decimal | None
    goal_fat_g: Decimal | None
    goal_carb_g: Decimal | None
    exclude_fast_food: bool
    notes: str | None
    dietary_restriction_codes: list[str]
    cuisine_codes: list[str]
    sunday_plan_reminder_enabled: bool
    reminder_hour_local: int
