from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import delete, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from bot.db.models import Cuisine, DietaryRestriction, UserCuisinePreference, UserDietaryRestriction, UserNotificationSettings, UserProfile
from bot.services.dto import ProfileView, RegistrationDraft


class ProfileRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_profile(self, *, user_id: uuid.UUID, draft: RegistrationDraft) -> None:
        stmt = (
            insert(UserProfile)
            .values(
                user_id=user_id,
                weekly_budget_rub=draft.weekly_budget_rub,
                household_size=draft.household_size,
                cooking_skill=draft.cooking_skill,
                max_cook_time_min=draft.max_cook_time_min,
                goal_kcal=draft.goal_kcal,
                goal_protein_g=draft.goal_protein_g,
                goal_fat_g=draft.goal_fat_g,
                goal_carb_g=draft.goal_carb_g,
                exclude_fast_food=draft.exclude_fast_food,
                notes=draft.notes,
            )
            .on_conflict_do_update(
                index_elements=[UserProfile.user_id],
                set_={
                    "weekly_budget_rub": draft.weekly_budget_rub,
                    "household_size": draft.household_size,
                    "cooking_skill": draft.cooking_skill,
                    "max_cook_time_min": draft.max_cook_time_min,
                    "goal_kcal": draft.goal_kcal,
                    "goal_protein_g": draft.goal_protein_g,
                    "goal_fat_g": draft.goal_fat_g,
                    "goal_carb_g": draft.goal_carb_g,
                    "exclude_fast_food": draft.exclude_fast_food,
                    "notes": draft.notes,
                },
            )
        )
        await self._session.execute(stmt)

    async def replace_dietary_restrictions(self, *, user_id: uuid.UUID, codes: list[str]) -> None:
        await self._session.execute(delete(UserDietaryRestriction).where(UserDietaryRestriction.user_id == user_id))
        if not codes:
            return
        result = await self._session.execute(
            select(DietaryRestriction.id, DietaryRestriction.code).where(DietaryRestriction.code.in_(codes))
        )
        code_to_id = {row.code: row.id for row in result}
        values = [{"user_id": user_id, "restriction_id": code_to_id[code]} for code in codes if code in code_to_id]
        if values:
            await self._session.execute(insert(UserDietaryRestriction).values(values))

    async def replace_cuisines(self, *, user_id: uuid.UUID, codes: list[str]) -> None:
        await self._session.execute(delete(UserCuisinePreference).where(UserCuisinePreference.user_id == user_id))
        if not codes:
            return
        result = await self._session.execute(select(Cuisine.id, Cuisine.code).where(Cuisine.code.in_(codes)))
        code_to_id = {row.code: row.id for row in result}
        values = []
        priority = len(codes)
        for code in codes:
            cuisine_id = code_to_id.get(code)
            if cuisine_id is None:
                continue
            values.append({"user_id": user_id, "cuisine_id": cuisine_id, "priority": priority})
            priority -= 1
        if values:
            await self._session.execute(insert(UserCuisinePreference).values(values))

    async def upsert_notification_settings(
        self, *, user_id: uuid.UUID, sunday_plan_reminder_enabled: bool, reminder_hour_local: int
    ) -> None:
        stmt = (
            insert(UserNotificationSettings)
            .values(
                user_id=user_id,
                sunday_plan_reminder_enabled=sunday_plan_reminder_enabled,
                reminder_hour_local=reminder_hour_local,
            )
            .on_conflict_do_update(
                index_elements=[UserNotificationSettings.user_id],
                set_={
                    "sunday_plan_reminder_enabled": sunday_plan_reminder_enabled,
                    "reminder_hour_local": reminder_hour_local,
                },
            )
        )
        await self._session.execute(stmt)

    async def get_profile_view(self, *, telegram_user_id: int) -> ProfileView | None:
        base = await self._session.execute(
            text(
                """
                SELECT
                  u.id AS user_id,
                  u.telegram_user_id,
                  p.weekly_budget_rub,
                  p.household_size,
                  p.cooking_skill,
                  p.max_cook_time_min,
                  p.goal_kcal,
                  p.goal_protein_g,
                  p.goal_fat_g,
                  p.goal_carb_g,
                  p.exclude_fast_food,
                  p.notes,
                  COALESCE(n.sunday_plan_reminder_enabled, TRUE) AS sunday_plan_reminder_enabled,
                  COALESCE(n.reminder_hour_local, 18) AS reminder_hour_local
                FROM users u
                JOIN user_profiles p ON p.user_id = u.id
                LEFT JOIN user_notification_settings n ON n.user_id = u.id
                WHERE u.telegram_user_id = :telegram_user_id
                """
            ),
            {"telegram_user_id": telegram_user_id},
        )
        base_row = base.first()
        if base_row is None:
            return None

        restrictions = await self._session.execute(
            text(
                """
                SELECT dr.code
                FROM user_dietary_restrictions udr
                JOIN dietary_restrictions dr ON dr.id = udr.restriction_id
                WHERE udr.user_id = :user_id
                ORDER BY dr.code
                """
            ),
            {"user_id": base_row.user_id},
        )
        cuisines = await self._session.execute(
            text(
                """
                SELECT c.code
                FROM user_cuisine_preferences ucp
                JOIN cuisines c ON c.id = ucp.cuisine_id
                WHERE ucp.user_id = :user_id
                ORDER BY ucp.priority DESC, c.code
                """
            ),
            {"user_id": base_row.user_id},
        )
        return ProfileView(
            telegram_user_id=base_row.telegram_user_id,
            weekly_budget_rub=Decimal(base_row.weekly_budget_rub),
            household_size=base_row.household_size,
            cooking_skill=base_row.cooking_skill,
            max_cook_time_min=base_row.max_cook_time_min,
            goal_kcal=Decimal(base_row.goal_kcal) if base_row.goal_kcal is not None else None,
            goal_protein_g=Decimal(base_row.goal_protein_g) if base_row.goal_protein_g is not None else None,
            goal_fat_g=Decimal(base_row.goal_fat_g) if base_row.goal_fat_g is not None else None,
            goal_carb_g=Decimal(base_row.goal_carb_g) if base_row.goal_carb_g is not None else None,
            exclude_fast_food=base_row.exclude_fast_food,
            notes=base_row.notes,
            dietary_restriction_codes=[r.code for r in restrictions.fetchall()],
            cuisine_codes=[c.code for c in cuisines.fetchall()],
            sunday_plan_reminder_enabled=base_row.sunday_plan_reminder_enabled,
            reminder_hour_local=base_row.reminder_hour_local,
        )
