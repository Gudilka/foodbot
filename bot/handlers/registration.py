from __future__ import annotations

from decimal import Decimal
from typing import Any

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State
from aiogram.types import CallbackQuery, Message

from bot.fsm.flow import next_state, prev_state, progress_caption, resolve_state
from bot.fsm.states import RegistrationStates
from bot.keyboards import bool_keyboard, multiselect_keyboard, nav_keyboard, profile_keyboard
from bot.services import RegistrationDraft, RegistrationService
from bot.utils import parse_decimal_in_range, parse_int_in_range, parse_optional_decimal

DEFAULTS: dict[str, Any] = {
    "weekly_budget_rub": "3000",
    "household_size": 1,
    "cooking_skill": 3,
    "max_cook_time_min": 60,
    "goal_kcal": None,
    "goal_protein_g": None,
    "goal_fat_g": None,
    "goal_carb_g": None,
    "exclude_fast_food": True,
    "dietary_restriction_codes": [],
    "cuisine_codes": [],
    "sunday_plan_reminder_enabled": True,
    "reminder_hour_local": 18,
    "notes": None,
    "mode": "create",
}


def create_registration_router(service: RegistrationService) -> Router:
    router = Router(name="registration")

    def _is_private_message(message: Message) -> bool:
        return message.chat.type == "private"

    async def _ensure_draft_context(message: Message, state: FSMContext) -> dict[str, Any]:
        data = await state.get_data()
        if "telegram_user_id" in data:
            return data
        draft_data = dict(DEFAULTS)
        draft_data.update(
            {
                "telegram_user_id": message.from_user.id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name,
                "language_code": message.from_user.language_code or "ru",
                "timezone": "Europe/Moscow",
            }
        )
        await state.set_data(draft_data)
        return draft_data

    async def _send_step_prompt(target: Message | CallbackQuery, state: FSMContext, step: State) -> None:
        data = await state.get_data()
        prefix = progress_caption(step)
        text = ""
        markup = nav_keyboard()
        if step == RegistrationStates.budget:
            text = f"{prefix}\nВведите бюджет на неделю в ₽ (500..100000)."
        elif step == RegistrationStates.household_size:
            text = f"{prefix}\nСколько человек в семье? (1..10)"
        elif step == RegistrationStates.dietary_restrictions:
            selected = set(data.get("dietary_restriction_codes", []))
            options = await service.list_restrictions()
            text = f"{prefix}\nВыберите ограничения (мультивыбор), затем Done."
            markup = multiselect_keyboard(prefix="reg:restriction", options=options, selected_codes=selected)
        elif step == RegistrationStates.cooking_skill:
            text = f"{prefix}\nУровень готовки (1..5)."
        elif step == RegistrationStates.max_cook_time:
            text = f"{prefix}\nМаксимум времени на рецепт в минутах (10..240)."
        elif step == RegistrationStates.goals_kbju:
            text = (
                f"{prefix}\nВведите 4 значения через пробел: `ккал белки жиры углеводы`.\n"
                "Для пропуска конкретного значения укажите `-`. Пример: `2200 120 70 200`"
            )
        elif step == RegistrationStates.exclude_fast_food:
            text = f"{prefix}\nИсключать фастфуд?"
            markup = bool_keyboard(prefix="reg:exclude")
        elif step == RegistrationStates.cuisine_preferences:
            selected = set(data.get("cuisine_codes", []))
            options = await service.list_cuisines()
            text = f"{prefix}\nВыберите предпочитаемые кухни (мультивыбор), затем Done."
            markup = multiselect_keyboard(prefix="reg:cuisine", options=options, selected_codes=selected)
        elif step == RegistrationStates.reminder_settings:
            phase = data.get("reminder_phase", "enabled")
            if phase == "enabled":
                text = f"{prefix}\nВключить воскресное напоминание о плане?"
                markup = bool_keyboard(prefix="reg:reminder_enabled")
            else:
                text = f"{prefix}\nВведите час напоминания (0..23)."
        elif step == RegistrationStates.notes:
            text = f"{prefix}\nКомментарий к профилю (или `-`, чтобы пропустить)."
        elif step == RegistrationStates.confirm:
            try:
                draft = RegistrationDraft(**{**DEFAULTS, **data})
                text = (
                    f"{prefix}\nПроверьте данные:\n"
                    f"- Бюджет: {draft.weekly_budget_rub} ₽\n"
                    f"- Семья: {draft.household_size}\n"
                    f"- Навык: {draft.cooking_skill}\n"
                    f"- Время: {draft.max_cook_time_min} мин\n"
                    f"- Ограничения: {', '.join(draft.dietary_restriction_codes) or 'нет'}\n"
                    f"- Кухни: {', '.join(draft.cuisine_codes) or 'не выбраны'}\n"
                    f"- Напоминание: {'вкл' if draft.sunday_plan_reminder_enabled else 'выкл'} {draft.reminder_hour_local}:00\n\n"
                    "Нажмите ✅ Done для сохранения."
                )
            except Exception:
                text = f"{prefix}\nОшибка в данных анкеты. Вернитесь назад и исправьте поля."
            markup = nav_keyboard(allow_skip=False, include_done=True)

        if isinstance(target, CallbackQuery):
            await target.message.answer(text, reply_markup=markup)
            await target.answer()
        else:
            await target.answer(text, reply_markup=markup)

    async def _move_to_next(target: Message | CallbackQuery, state: FSMContext, current: State) -> None:
        nxt = next_state(current)
        await state.set_state(nxt)
        await _send_step_prompt(target, state, nxt)

    async def _start_onboarding(message: Message, state: FSMContext, *, mode: str) -> None:
        await state.clear()
        draft_data = dict(DEFAULTS)
        draft_data.update(
            {
                "mode": mode,
                "telegram_user_id": message.from_user.id,
                "username": message.from_user.username,
                "first_name": message.from_user.first_name,
                "last_name": message.from_user.last_name,
                "language_code": message.from_user.language_code or "ru",
                "timezone": "Europe/Moscow",
            }
        )
        if mode == "update":
            preloaded = await service.preload_draft(telegram_user_id=message.from_user.id, tg_user=message.from_user)
            if preloaded:
                draft_data.update(preloaded.model_dump())
        await state.set_data(draft_data)
        await state.set_state(RegistrationStates.budget)
        await _send_step_prompt(message, state, RegistrationStates.budget)

    async def _handle_cancel(message: Message, state: FSMContext) -> None:
        await service.cancel_onboarding(telegram_user_id=message.from_user.id)
        await state.clear()
        await message.answer("Анкета отменена. Используйте /start для начала.")

    @router.message(Command("start"))
    async def cmd_start(message: Message, state: FSMContext) -> None:
        if not _is_private_message(message):
            return
        _, is_new = await service.ensure_user(message.from_user)
        if is_new:
            await message.answer("Привет! Настроим профиль за 1-2 минуты.")
            await _start_onboarding(message, state, mode="create")
            return
        profile = await service.get_profile(telegram_user_id=message.from_user.id)
        if profile is None:
            await message.answer("Профиль не заполнен. Запустим анкету.")
            await _start_onboarding(message, state, mode="create")
            return
        await state.clear()
        await message.answer(service.format_profile(profile), reply_markup=profile_keyboard())

    @router.message(Command("profile"))
    async def cmd_profile(message: Message, state: FSMContext) -> None:
        if not _is_private_message(message):
            return
        await state.clear()
        profile = await service.get_profile(telegram_user_id=message.from_user.id)
        if profile is None:
            await message.answer("Профиль пока не заполнен. Используйте /start.")
            return
        await message.answer(service.format_profile(profile), reply_markup=profile_keyboard())

    @router.message(Command("edit_profile"))
    async def cmd_edit_profile(message: Message, state: FSMContext) -> None:
        if not _is_private_message(message):
            return
        await _start_onboarding(message, state, mode="update")

    @router.message(Command("cancel"))
    async def cmd_cancel(message: Message, state: FSMContext) -> None:
        if not _is_private_message(message):
            return
        await _handle_cancel(message, state)

    @router.callback_query(F.data == "reg:action:edit_profile")
    async def cb_edit_profile(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None or callback.message.chat.type != "private":
            await callback.answer()
            return
        await callback.answer()
        await _start_onboarding(callback.message, state, mode="update")

    @router.callback_query(F.data == "reg:action:cancel")
    async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None or callback.message.chat.type != "private":
            await callback.answer()
            return
        await callback.answer()
        await _handle_cancel(callback.message, state)

    @router.callback_query(F.data == "reg:action:back")
    async def cb_back(callback: CallbackQuery, state: FSMContext) -> None:
        current = await state.get_state()
        if current is None:
            await callback.answer()
            return
        prev = prev_state(resolve_state(current))
        await state.set_state(prev)
        await _send_step_prompt(callback, state, prev)

    def _apply_skip(state_name: str, data: dict[str, Any]) -> dict[str, Any]:
        if state_name.endswith(":budget"):
            data["weekly_budget_rub"] = DEFAULTS["weekly_budget_rub"]
        elif state_name.endswith(":household_size"):
            data["household_size"] = DEFAULTS["household_size"]
        elif state_name.endswith(":dietary_restrictions"):
            data["dietary_restriction_codes"] = []
        elif state_name.endswith(":cooking_skill"):
            data["cooking_skill"] = DEFAULTS["cooking_skill"]
        elif state_name.endswith(":max_cook_time"):
            data["max_cook_time_min"] = DEFAULTS["max_cook_time_min"]
        elif state_name.endswith(":goals_kbju"):
            data["goal_kcal"] = None
            data["goal_protein_g"] = None
            data["goal_fat_g"] = None
            data["goal_carb_g"] = None
        elif state_name.endswith(":exclude_fast_food"):
            data["exclude_fast_food"] = DEFAULTS["exclude_fast_food"]
        elif state_name.endswith(":cuisine_preferences"):
            data["cuisine_codes"] = []
        elif state_name.endswith(":reminder_settings"):
            data["sunday_plan_reminder_enabled"] = DEFAULTS["sunday_plan_reminder_enabled"]
            data["reminder_hour_local"] = DEFAULTS["reminder_hour_local"]
            data["reminder_phase"] = "enabled"
        elif state_name.endswith(":notes"):
            data["notes"] = None
        return data

    @router.callback_query(F.data == "reg:action:skip")
    async def cb_skip(callback: CallbackQuery, state: FSMContext) -> None:
        current_state = await state.get_state()
        if current_state is None:
            await callback.answer()
            return
        data = await state.get_data()
        data = _apply_skip(current_state, data)
        await state.set_data(data)
        current = resolve_state(current_state)
        await service.log_step_completed(telegram_user_id=callback.from_user.id, step_name=current_state)
        await _move_to_next(callback, state, current)

    @router.callback_query(F.data == "reg:action:done")
    async def cb_done(callback: CallbackQuery, state: FSMContext) -> None:
        current_state = await state.get_state()
        if current_state is None:
            await callback.answer()
            return
        if current_state.endswith(":dietary_restrictions") or current_state.endswith(":cuisine_preferences"):
            await service.log_step_completed(telegram_user_id=callback.from_user.id, step_name=current_state)
            await _move_to_next(callback, state, resolve_state(current_state))
            return
        if current_state.endswith(":confirm"):
            data = await state.get_data()
            try:
                draft = RegistrationDraft(**{**DEFAULTS, **data})
            except Exception:
                await callback.answer("Данные анкеты некорректны")
                return
            await service.save_profile(draft=draft, mode=data.get("mode", "create"))
            await state.clear()
            await callback.message.answer("Профиль сохранён. Используйте /profile для просмотра.")
            await callback.answer()
            return
        await callback.answer()

    @router.callback_query(F.data == "reg:confirm")
    async def cb_confirm(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None:
            await callback.answer()
            return
        current_state = await state.get_state()
        if current_state is None or not current_state.endswith(":confirm"):
            await callback.answer("Сейчас нельзя подтвердить")
            return
        data = await state.get_data()
        try:
            draft = RegistrationDraft(**{**DEFAULTS, **data})
        except Exception:
            await callback.answer("Данные анкеты некорректны")
            return
        await service.save_profile(draft=draft, mode=data.get("mode", "create"))
        await state.clear()
        await callback.message.answer("Профиль сохранён. Используйте /profile для просмотра.")
        await callback.answer()

    @router.callback_query(F.data.startswith("reg:step:"))
    async def cb_step(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None:
            await callback.answer()
            return
        step_name = callback.data.split(":")[-1]
        allowed = {
            "budget",
            "household_size",
            "dietary_restrictions",
            "cooking_skill",
            "max_cook_time",
            "goals_kbju",
            "exclude_fast_food",
            "cuisine_preferences",
            "reminder_settings",
            "notes",
            "confirm",
        }
        if step_name not in allowed:
            await callback.answer("Неизвестный шаг")
            return
        state_name = f"RegistrationStates:{step_name}"
        target_state = resolve_state(state_name)
        await state.set_state(target_state)
        await _send_step_prompt(callback, state, target_state)

    @router.callback_query(F.data.startswith("reg:restriction:"))
    async def cb_toggle_restriction(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None:
            await callback.answer()
            return
        data = await _ensure_draft_context(callback.message, state)
        code = callback.data.split(":")[-1]
        selected = set(data.get("dietary_restriction_codes", []))
        if code in selected:
            selected.remove(code)
        else:
            selected.add(code)
        data["dietary_restriction_codes"] = list(selected)
        await state.set_data(data)
        await _send_step_prompt(callback, state, RegistrationStates.dietary_restrictions)

    @router.callback_query(F.data.startswith("reg:cuisine:"))
    async def cb_toggle_cuisine(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None:
            await callback.answer()
            return
        data = await _ensure_draft_context(callback.message, state)
        code = callback.data.split(":")[-1]
        selected = set(data.get("cuisine_codes", []))
        if code in selected:
            selected.remove(code)
        else:
            selected.add(code)
        data["cuisine_codes"] = list(selected)
        await state.set_data(data)
        await _send_step_prompt(callback, state, RegistrationStates.cuisine_preferences)

    @router.callback_query(F.data.startswith("reg:exclude:"))
    async def cb_exclude_fast_food(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None:
            await callback.answer()
            return
        data = await _ensure_draft_context(callback.message, state)
        data["exclude_fast_food"] = callback.data.endswith(":yes")
        await state.set_data(data)
        await service.log_step_completed(telegram_user_id=callback.from_user.id, step_name="exclude_fast_food")
        await _move_to_next(callback, state, RegistrationStates.exclude_fast_food)

    @router.callback_query(F.data.startswith("reg:reminder_enabled:"))
    async def cb_reminder_enabled(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None:
            await callback.answer()
            return
        data = await _ensure_draft_context(callback.message, state)
        data["sunday_plan_reminder_enabled"] = callback.data.endswith(":yes")
        data["reminder_phase"] = "hour"
        await state.set_data(data)
        await _send_step_prompt(callback, state, RegistrationStates.reminder_settings)

    async def _handle_text_step(message: Message, state: FSMContext, current_state: str) -> bool:
        data = await _ensure_draft_context(message, state)
        try:
            if current_state.endswith(":budget"):
                data["weekly_budget_rub"] = str(
                    parse_decimal_in_range(
                        message.text,
                        min_value=Decimal("500"),
                        max_value=Decimal("100000"),
                        field_name="Бюджет",
                    )
                )
            elif current_state.endswith(":household_size"):
                data["household_size"] = parse_int_in_range(
                    message.text, min_value=1, max_value=10, field_name="Размер семьи"
                )
            elif current_state.endswith(":cooking_skill"):
                data["cooking_skill"] = parse_int_in_range(
                    message.text, min_value=1, max_value=5, field_name="Уровень готовки"
                )
            elif current_state.endswith(":max_cook_time"):
                data["max_cook_time_min"] = parse_int_in_range(
                    message.text, min_value=10, max_value=240, field_name="Время готовки"
                )
            elif current_state.endswith(":goals_kbju"):
                parts = message.text.strip().split()
                if len(parts) != 4:
                    raise ValueError("Введите 4 значения: ккал белки жиры углеводы")
                data["goal_kcal"] = parse_optional_decimal(parts[0], min_value=Decimal("0"), field_name="Ккал")
                data["goal_protein_g"] = parse_optional_decimal(parts[1], min_value=Decimal("0"), field_name="Белки")
                data["goal_fat_g"] = parse_optional_decimal(parts[2], min_value=Decimal("0"), field_name="Жиры")
                data["goal_carb_g"] = parse_optional_decimal(parts[3], min_value=Decimal("0"), field_name="Углеводы")
            elif current_state.endswith(":reminder_settings"):
                phase = data.get("reminder_phase", "enabled")
                if phase != "hour":
                    await message.answer("Сначала выберите включение напоминаний кнопками.")
                    return True
                data["reminder_hour_local"] = parse_int_in_range(
                    message.text, min_value=0, max_value=23, field_name="Час напоминания"
                )
                data["reminder_phase"] = "enabled"
            elif current_state.endswith(":notes"):
                note = message.text.strip()
                data["notes"] = None if note == "-" else note
            else:
                return False
        except ValueError as exc:
            await message.answer(f"Ошибка: {exc}")
            await _send_step_prompt(message, state, resolve_state(current_state))
            return True

        await state.set_data(data)
        await service.log_step_completed(telegram_user_id=message.from_user.id, step_name=current_state)
        await _move_to_next(message, state, resolve_state(current_state))
        return True

    @router.message(F.text)
    async def wizard_text_router(message: Message, state: FSMContext) -> None:
        if not _is_private_message(message):
            return
        current_state = await state.get_state()
        if current_state is None:
            return
        await _handle_text_step(message, state, current_state)

    return router
