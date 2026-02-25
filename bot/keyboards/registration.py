from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.services.registration_service import ReferenceOption


def nav_keyboard(*, allow_skip: bool = True, include_done: bool = False) -> InlineKeyboardMarkup:
    row: list[InlineKeyboardButton] = [
        InlineKeyboardButton(text="⬅️ Back", callback_data="reg:action:back"),
    ]
    if allow_skip:
        row.append(InlineKeyboardButton(text="⏭ Skip", callback_data="reg:action:skip"))
    row.append(InlineKeyboardButton(text="❌ Cancel", callback_data="reg:action:cancel"))
    rows = [row]
    if include_done:
        rows.append([InlineKeyboardButton(text="✅ Done", callback_data="reg:confirm")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def bool_keyboard(prefix: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Да", callback_data=f"{prefix}:yes"),
                InlineKeyboardButton(text="Нет", callback_data=f"{prefix}:no"),
            ],
            [
                InlineKeyboardButton(text="⬅️ Back", callback_data="reg:action:back"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="reg:action:cancel"),
            ],
        ]
    )


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
    action_row = [InlineKeyboardButton(text="✅ Done", callback_data="reg:action:done")]
    action_row.append(InlineKeyboardButton(text="⬅️ Back", callback_data="reg:action:back"))
    rows.append(action_row)
    if add_skip:
        rows.append(
            [
                InlineKeyboardButton(text="⏭ Skip", callback_data="reg:action:skip"),
                InlineKeyboardButton(text="❌ Cancel", callback_data="reg:action:cancel"),
            ]
        )
    else:
        rows.append([InlineKeyboardButton(text="❌ Cancel", callback_data="reg:action:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать профиль", callback_data="reg:action:edit_profile")],
        ]
    )
