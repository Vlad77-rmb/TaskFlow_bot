"""Простой инлайн-календарь на месяц + выбор времени.

Формат callback_data:
    cal:nav:<YYYY-MM>        — перейти на месяц
    cal:day:<YYYY-MM-DD>     — выбрать день
    cal:ignore               — заглушка для пустых ячеек
    cal:time:<HH:MM>         — выбрать время (шаг 30 мин)
    cal:manual               — ввести вручную
"""

from __future__ import annotations

import calendar
from datetime import date, datetime

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

RU_MONTHS = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
RU_WEEKDAYS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def month_kb(year: int, month: int, today: date | None = None) -> InlineKeyboardMarkup:
    """Клавиатура календаря на месяц."""
    today = today or date.today()
    builder = InlineKeyboardBuilder()

    # Заголовок: ← Октябрь 2026 →
    prev_y, prev_m = (year - 1, 12) if month == 1 else (year, month - 1)
    next_y, next_m = (year + 1, 1) if month == 12 else (year, month + 1)

    builder.row(
        InlineKeyboardButton(text="◀", callback_data=f"cal:nav:{prev_y:04d}-{prev_m:02d}"),
        InlineKeyboardButton(
            text=f"{RU_MONTHS[month - 1]} {year}",
            callback_data="cal:ignore",
        ),
        InlineKeyboardButton(text="▶", callback_data=f"cal:nav:{next_y:04d}-{next_m:02d}"),
    )

    # Дни недели
    builder.row(*[InlineKeyboardButton(text=d, callback_data="cal:ignore") for d in RU_WEEKDAYS])

    # Сетка дней
    cal = calendar.Calendar(firstweekday=0)  # 0 = понедельник
    for week in cal.monthdatescalendar(year, month):
        row_buttons = []
        for day in week:
            if day.month != month:
                row_buttons.append(
                    InlineKeyboardButton(text=" ", callback_data="cal:ignore")
                )
                continue
            # Прошлые даты делаем некликабельными (или оставляем — на вкус)
            if day < today:
                row_buttons.append(
                    InlineKeyboardButton(text=f"·{day.day}·", callback_data="cal:past")
                )
            else:
                label = f"[{day.day}]" if day == today else str(day.day)
                row_buttons.append(
                    InlineKeyboardButton(
                        text=label, callback_data=f"cal:day:{day.isoformat()}"
                    )
                )
        builder.row(*row_buttons)

    # Нижний ряд — «Пропустить»
    builder.row(
        InlineKeyboardButton(text="⏭ Без напоминания", callback_data="cal:skip")
    )
    return builder.as_markup()


def time_kb(day: date) -> InlineKeyboardMarkup:
    """Выбор времени с шагом 30 минут (с 06:00 до 23:30)."""
    builder = InlineKeyboardBuilder()
    slots: list[str] = []
    for hour in range(6, 24):
        for minute in (0, 30):
            slots.append(f"{hour:02d}:{minute:02d}")

    # По 4 кнопки в ряд
    row: list[InlineKeyboardButton] = []
    for slot in slots:
        row.append(
            InlineKeyboardButton(
                text=slot, callback_data=f"cal:time:{day.isoformat()}:{slot}"
            )
        )
        if len(row) == 4:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)

    builder.row(
        InlineKeyboardButton(text="✏️ Ввести вручную", callback_data="cal:manual"),
        InlineKeyboardButton(text="⬅ Назад", callback_data="cal:back"),
    )
    return builder.as_markup()