from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from aiogram.types import User as TgUser
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from bot.repositories import EventLogRepository, NotificationSettingsRepository, ProfileRepository, RestrictionsRepository, UserRepository
from bot.services.dto import ProfileView, RegistrationDraft

DIET_TYPE_LABELS: dict[str, str] = {
    "omnivore": "Всеядное",
    "vegetarian": "Вегетарианское",
    "vegan": "Веганское",
    "pescatarian": "Пескетарианское",
    "other": "Другое",
}

NUTRITION_GOAL_LABELS: dict[str, str] = {
    "weight_loss": "Снижение веса",
    "maintenance": "Поддержание формы",
    "muscle_gain": "Набор мышечной массы",
    "health_support": "Поддержка здоровья",
    "medical_diet": "Лечебная диета",
    "other": "Другое",
}

RESTRICTION_LABELS: dict[str, str] = {
    "lactose_free": "Без лактозы",
    "gluten_free": "Без глютена",
    "nut_free": "Без орехов",
    "halal": "Халяль",
    "vegetarian": "Вегетарианское",
    "vegan": "Веганское",
}

RESTRICTION_CODES_EXCLUDED_FROM_STEP = {"vegan", "vegetarian"}


@dataclass(frozen=True)
class ReferenceOption:
    code: str
    name: str


class RegistrationService:
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def ensure_user(self, tg_user: TgUser) -> tuple[str, bool]:
        async with self._session_factory() as session:
            user_repo = UserRepository(session)
            notif_repo = NotificationSettingsRepository(session)
            event_repo = EventLogRepository(session)

            existing = await user_repo.get_by_telegram_user_id(tg_user.id)
            user_id = await user_repo.upsert_user(
                telegram_user_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                last_name=tg_user.last_name,
                language_code=tg_user.language_code or "ru",
            )
            await notif_repo.upsert_defaults(user_id=user_id)

            if existing is None:
                await event_repo.log_event(user_id=user_id, event_name="onboarding_started", payload={"entrypoint": "/start"})

            await session.commit()
            return user_id, existing is None

    async def save_profile(self, *, draft: RegistrationDraft, mode: str = "create") -> str:
        async with self._session_factory() as session:
            user_repo = UserRepository(session)
            profile_repo = ProfileRepository(session)
            event_repo = EventLogRepository(session)

            user_id = await user_repo.upsert_user(
                telegram_user_id=draft.telegram_user_id,
                username=draft.username,
                first_name=draft.first_name,
                last_name=draft.last_name,
                language_code=draft.language_code,
            )
            await profile_repo.upsert_profile(user_id=user_id, draft=draft)
            await profile_repo.replace_dietary_restrictions(user_id=user_id, codes=draft.dietary_restriction_codes)
            await profile_repo.replace_cuisines(user_id=user_id, codes=draft.cuisine_codes)
            await profile_repo.upsert_notification_settings(
                user_id=user_id,
                sunday_plan_reminder_enabled=draft.sunday_plan_reminder_enabled,
                reminder_hour_local=draft.reminder_hour_local,
            )
            event_name = "profile_updated" if mode == "update" else "onboarding_completed"
            await event_repo.log_event(user_id=user_id, event_name=event_name, payload={"mode": mode})
            await session.commit()
            return user_id

    async def cancel_onboarding(self, *, telegram_user_id: int) -> None:
        async with self._session_factory() as session:
            user_repo = UserRepository(session)
            event_repo = EventLogRepository(session)
            user = await user_repo.get_by_telegram_user_id(telegram_user_id)
            await event_repo.log_event(
                user_id=user.id if user else None,
                event_name="onboarding_cancelled",
                payload={"telegram_user_id": telegram_user_id},
            )
            await session.commit()

    async def log_step_completed(self, *, telegram_user_id: int, step_name: str) -> None:
        async with self._session_factory() as session:
            user_repo = UserRepository(session)
            event_repo = EventLogRepository(session)
            user = await user_repo.get_by_telegram_user_id(telegram_user_id)
            await event_repo.log_event(
                user_id=user.id if user else None,
                event_name="onboarding_step_completed",
                payload={"step": step_name},
            )
            await session.commit()

    async def get_profile(self, *, telegram_user_id: int) -> ProfileView | None:
        async with self._session_factory() as session:
            profile_repo = ProfileRepository(session)
            return await profile_repo.get_profile_view(telegram_user_id=telegram_user_id)

    async def preload_draft(self, *, telegram_user_id: int, tg_user: TgUser) -> RegistrationDraft | None:
        profile = await self.get_profile(telegram_user_id=telegram_user_id)
        if profile is None:
            return None
        return RegistrationDraft(
            telegram_user_id=tg_user.id,
            username=tg_user.username,
            first_name=tg_user.first_name,
            last_name=tg_user.last_name,
            language_code=tg_user.language_code or "ru",
            weekly_budget_rub=profile.weekly_budget_rub,
            diet_type=profile.diet_type,
            nutrition_goal=profile.nutrition_goal,
            household_size=profile.household_size,
            cooking_skill=profile.cooking_skill or 3,
            max_cook_time_min=profile.max_cook_time_min or 60,
            goal_kcal=profile.goal_kcal,
            goal_protein_g=profile.goal_protein_g,
            goal_fat_g=profile.goal_fat_g,
            goal_carb_g=profile.goal_carb_g,
            exclude_fast_food=profile.exclude_fast_food,
            notes=profile.notes,
            dietary_restriction_codes=profile.dietary_restriction_codes,
            cuisine_codes=profile.cuisine_codes,
            sunday_plan_reminder_enabled=profile.sunday_plan_reminder_enabled,
            reminder_hour_local=profile.reminder_hour_local,
        )

    async def list_restrictions(self) -> list[ReferenceOption]:
        async with self._session_factory() as session:
            repo = RestrictionsRepository(session)
            items = await repo.list_restrictions()
            options = [ReferenceOption(code=i.code, name=i.name) for i in items]
            return self.filter_restriction_options(options)

    @staticmethod
    def filter_restriction_options(options: list[ReferenceOption]) -> list[ReferenceOption]:
        return [o for o in options if o.code not in RESTRICTION_CODES_EXCLUDED_FROM_STEP]

    @staticmethod
    def diet_type_label(code: str | None) -> str:
        if not code:
            return "Не выбрано"
        return DIET_TYPE_LABELS.get(code, code)

    @staticmethod
    def nutrition_goal_label(code: str | None) -> str:
        if not code:
            return "Не выбрано"
        return NUTRITION_GOAL_LABELS.get(code, code)

    @staticmethod
    def restriction_label(code: str) -> str:
        return RESTRICTION_LABELS.get(code, code)

    @classmethod
    def format_profile(cls, profile: ProfileView) -> str:
        restrictions = (
            ", ".join(cls.restriction_label(code) for code in profile.dietary_restriction_codes)
            if profile.dietary_restriction_codes
            else "нет"
        )
        return (
            "Ваш профиль:\n"
            f"- Бюджет на неделю: {Decimal(profile.weekly_budget_rub)} ₽\n"
            f"- Тип питания: {cls.diet_type_label(profile.diet_type)}\n"
            f"- Цель питания: {cls.nutrition_goal_label(profile.nutrition_goal)}\n"
            f"- Количество человек: {profile.household_size}\n"
            f"- Аллергии и ограничения: {restrictions}"
        )
