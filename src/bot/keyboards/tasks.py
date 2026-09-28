from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from src.db.models.task import Priority, Task


def priority_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🟢 Низкий", callback_data="prio:low"),
                InlineKeyboardButton(text="🟡 Средний", callback_data="prio:medium"),
                InlineKeyboardButton(text="🔴 Высокий", callback_data="prio:high"),
            ],
        ]
    )


def skip_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="⏭ Пропустить", callback_data="skip")],
        ]
    )


def task_actions_kb(task: Task) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Выполнено", callback_data=f"task:done:{task.id}"
                ),
                InlineKeyboardButton(
                    text="🗑 Удалить", callback_data=f"task:delete:{task.id}"
                ),
            ],
        ]
    )


PRIORITY_BY_CODE = {
    "low": Priority.LOW,
    "medium": Priority.MEDIUM,
    "high": Priority.HIGH,
}


def priority_emoji(priority: Priority) -> str:
    return {
        Priority.LOW: "🟢",
        Priority.MEDIUM: "🟡",
        Priority.HIGH: "🔴",
    }[priority]