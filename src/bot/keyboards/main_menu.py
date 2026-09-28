from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu() -> ReplyKeyboardMarkup:
    """Постоянное меню под полем ввода."""
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="➕ Новая задача"),
                KeyboardButton(text="📋 Мои задачи"),
            ],
            [
                KeyboardButton(text="❌ Отмена"),
                KeyboardButton(text="📖 Справка"),
            ],
        ],
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Выбери действие или напиши /add",
    )