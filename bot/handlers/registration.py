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
from bot.keyboards import multiselect_keyboard, nav_keyboard, profile_keyboard, single_select_keyboard
from bot.services import RegistrationDraft, RegistrationService
from bot.services.registration_service import DIET_TYPE_LABELS, NUTRITION_GOAL_LABELS, ReferenceOption
from bot.utils import parse_decimal_in_range, parse_int_in_range

DEFAULTS: dict[str, Any] = {
    "weekly_budget_rub": "3000",
    "diet_type": "omnivore",
    "nutrition_goal": "maintenance",
    "household_size": 1,
    "dietary_restriction_codes": [],
    # Legacy fields kept in payload for compatibility.
    "cooking_skill": 3,
    "max_cook_time_min": 60,
    "goal_kcal": None,
    "goal_protein_g": None,
    "goal_fat_g": None,
    "goal_carb_g": None,
    "exclude_fast_food": True,
    "notes": None,
    "cuisine_codes": [],
    "sunday_plan_reminder_enabled": True,
    "reminder_hour_local": 18,
    "mode": "create",
}

DIET_TYPE_OPTIONS = [
    ReferenceOption(code="omnivore", name="Всеядное"),
    ReferenceOption(code="vegetarian", name="Вегетарианское"),
    ReferenceOption(code="vegan", name="Веганское"),
    ReferenceOption(code="pescatarian", name="Пескетарианское"),
    ReferenceOption(code="other", name="Другое"),
]

NUTRITION_GOAL_OPTIONS = [
    ReferenceOption(code="weight_loss", name="Снижение веса"),
    ReferenceOption(code="maintenance", name="Поддержание формы"),
    ReferenceOption(code="muscle_gain", name="Набор мышечной массы"),
    ReferenceOption(code="health_support", name="Поддержка здоровья"),
    ReferenceOption(code="medical_diet", name="Лечебная диета"),
    ReferenceOption(code="other", name="Другое"),
]


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
        elif step == RegistrationStates.diet_type:
            text = f"{prefix}\nВыберите тип питания."
            markup = single_select_keyboard(
                prefix="reg:diet_type",
                options=DIET_TYPE_OPTIONS,
                selected_code=data.get("diet_type"),
            )
        elif step == RegistrationStates.nutrition_goal:
            text = f"{prefix}\nВыберите цель питания."
            markup = single_select_keyboard(
                prefix="reg:nutrition_goal",
                options=NUTRITION_GOAL_OPTIONS,
                selected_code=data.get("nutrition_goal"),
            )
        elif step == RegistrationStates.household_size:
            text = f"{prefix}\nСколько человек в семье? (1..10)"
        elif step == RegistrationStates.dietary_restrictions:
            selected = set(data.get("dietary_restriction_codes", []))
            options = await service.list_restrictions()
            text = f"{prefix}\nВыберите аллергии и ограничения (мультивыбор), затем «Готово»."
            markup = multiselect_keyboard(prefix="reg:restriction", options=options, selected_codes=selected)
        elif step == RegistrationStates.confirm:
            try:
                draft = RegistrationDraft(**{**DEFAULTS, **data})
                selected_restrictions = [service.restriction_label(code) for code in draft.dietary_restriction_codes]
                text = (
                    f"{prefix}\nПроверьте данные:\n"
                    f"- Бюджет: {draft.weekly_budget_rub} ₽\n"
                    f"- Тип питания: {DIET_TYPE_LABELS.get(draft.diet_type or '', 'Не выбрано')}\n"
                    f"- Цель питания: {NUTRITION_GOAL_LABELS.get(draft.nutrition_goal or '', 'Не выбрано')}\n"
                    f"- Количество человек: {draft.household_size}\n"
                    f"- Аллергии и ограничения: {', '.join(selected_restrictions) or 'нет'}\n\n"
                    "Нажмите «✅ Готово», чтобы сохранить."
                )
            except Exception:
                text = f"{prefix}\nОшибка в данных анкеты. Вернитесь назад и проверьте шаги."
            markup = nav_keyboard(allow_skip=False, include_done=True)

        if isinstance(target, CallbackQuery):
            if target.message is None:
                await target.answer()
                return
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
        await message.answer("Анкета отменена. Используйте /start, чтобы начать заново.")

    @router.message(Command("start"))
    async def cmd_start(message: Message, state: FSMContext) -> None:
        if not _is_private_message(message):
            return
        _, is_new = await service.ensure_user(message.from_user)
        if is_new:
            await message.answer("Привет! Настроим профиль. Это займет около минуты.")
            await _start_onboarding(message, state, mode="create")
            return
        profile = await service.get_profile(telegram_user_id=message.from_user.id)
        if profile is None:
            await message.answer("Профиль пока не заполнен. Запускаю анкету.")
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
        elif state_name.endswith(":diet_type"):
            data["diet_type"] = DEFAULTS["diet_type"]
        elif state_name.endswith(":nutrition_goal"):
            data["nutrition_goal"] = DEFAULTS["nutrition_goal"]
        elif state_name.endswith(":household_size"):
            data["household_size"] = DEFAULTS["household_size"]
        elif state_name.endswith(":dietary_restrictions"):
            data["dietary_restriction_codes"] = []
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
        if current_state.endswith(":dietary_restrictions"):
            await service.log_step_completed(telegram_user_id=callback.from_user.id, step_name=current_state)
            await _move_to_next(callback, state, resolve_state(current_state))
            return
        await callback.answer()

    @router.callback_query(F.data == "reg:confirm")
    async def cb_confirm(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None:
            await callback.answer()
            return
        current_state = await state.get_state()
        if current_state is None or not current_state.endswith(":confirm"):
            await callback.answer("Сейчас подтверждение недоступно")
            return
        data = await state.get_data()
        try:
            draft = RegistrationDraft(**{**DEFAULTS, **data})
        except Exception:
            await callback.answer("Данные анкеты некорректны")
            return
        await service.save_profile(draft=draft, mode=data.get("mode", "create"))
        await state.clear()
        await callback.message.answer("Профиль сохранен. Используйте /profile для просмотра.")
        await callback.answer()

    @router.callback_query(F.data.startswith("reg:step:"))
    async def cb_step(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None:
            await callback.answer()
            return
        step_name = callback.data.split(":")[-1]
        allowed = {"budget", "diet_type", "nutrition_goal", "household_size", "dietary_restrictions", "confirm"}
        if step_name not in allowed:
            await callback.answer("Неизвестный шаг")
            return
        state_name = f"RegistrationStates:{step_name}"
        target_state = resolve_state(state_name)
        await state.set_state(target_state)
        await _send_step_prompt(callback, state, target_state)

    @router.callback_query(F.data.startswith("reg:diet_type:"))
    async def cb_diet_type(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None:
            await callback.answer()
            return
        data = await _ensure_draft_context(callback.message, state)
        selected = callback.data.split(":")[-1]
        data["diet_type"] = selected
        await state.set_data(data)
        await service.log_step_completed(telegram_user_id=callback.from_user.id, step_name="diet_type")
        await _move_to_next(callback, state, RegistrationStates.diet_type)

    @router.callback_query(F.data.startswith("reg:nutrition_goal:"))
    async def cb_nutrition_goal(callback: CallbackQuery, state: FSMContext) -> None:
        if callback.message is None:
            await callback.answer()
            return
        data = await _ensure_draft_context(callback.message, state)
        selected = callback.data.split(":")[-1]
        data["nutrition_goal"] = selected
        await state.set_data(data)
        await service.log_step_completed(telegram_user_id=callback.from_user.id, step_name="nutrition_goal")
        await _move_to_next(callback, state, RegistrationStates.nutrition_goal)

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
        data["dietary_restriction_codes"] = sorted(selected)
        await state.set_data(data)
        await _send_step_prompt(callback, state, RegistrationStates.dietary_restrictions)

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
                    message.text, min_value=1, max_value=10, field_name="Количество человек"
                )
            else:
                await message.answer("На этом шаге используйте кнопки под сообщением.")
                return True
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
