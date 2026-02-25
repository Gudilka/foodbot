from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.services.registration_service import ReferenceOption


def nav_keyboard(*, allow_skip: bool = True, include_done: bool = False) -> InlineKeyboardMarkup:
    row: list[InlineKeyboardButton] = [InlineKeyboardButton(text="⬅️ Назад", callback_data="reg:action:back")]
    if allow_skip:
        row.append(InlineKeyboardButton(text="⏭ Пропустить", callback_data="reg:action:skip"))
    row.append(InlineKeyboardButton(text="❌ Отмена", callback_data="reg:action:cancel"))
    rows = [row]
    if include_done:
        rows.append([InlineKeyboardButton(text="✅ Готово", callback_data="reg:confirm")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def single_select_keyboard(
    *,
    prefix: str,
    options: list[ReferenceOption],
    selected_code: str | None = None,
    allow_skip: bool = True,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for option in options:
        checked = "✅ " if option.code == selected_code else ""
        rows.append([InlineKeyboardButton(text=f"{checked}{option.name}", callback_data=f"{prefix}:{option.code}")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="reg:action:back")])
    if allow_skip:
        rows.append(
            [
                InlineKeyboardButton(text="⏭ Пропустить", callback_data="reg:action:skip"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="reg:action:cancel"),
            ]
        )
    else:
        rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="reg:action:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def multiselect_keyboard(
    *,
    prefix: str,
    options: list[ReferenceOption],
    selected_codes: set[str],
    add_skip: bool = True,
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    for option in options:
        checked = "✅ " if option.code in selected_codes else ""
        rows.append([InlineKeyboardButton(text=f"{checked}{option.name}", callback_data=f"{prefix}:{option.code}")])
    action_row = [InlineKeyboardButton(text="✅ Готово", callback_data="reg:action:done")]
    action_row.append(InlineKeyboardButton(text="⬅️ Назад", callback_data="reg:action:back"))
    rows.append(action_row)
    if add_skip:
        rows.append(
            [
                InlineKeyboardButton(text="⏭ Пропустить", callback_data="reg:action:skip"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="reg:action:cancel"),
            ]
        )
    else:
        rows.append([InlineKeyboardButton(text="❌ Отмена", callback_data="reg:action:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✏️ Редактировать профиль", callback_data="reg:action:edit_profile")]]
    )
