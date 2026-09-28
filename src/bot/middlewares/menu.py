from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from src.bot.keyboards.main_menu import main_menu


class MenuMiddleware(BaseMiddleware):
    """Автоматически добавляет Reply-клавиатуру к сообщениям бота."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        result = await handler(event, data)

        # Если бот отправил сообщение — прикрепляем меню
        # result — это объект Message, который вернул хендлер
        if isinstance(result, Message):
            try:
                await result.edit_reply_markup(reply_markup=main_menu())
            except Exception:
                # Некоторые сообщения нельзя редактировать — игнорируем
                pass

        return result