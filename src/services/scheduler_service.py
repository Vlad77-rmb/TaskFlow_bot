import logging
from datetime import datetime, timezone

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.bot import texts
from src.bot.keyboards import task_actions_kb
from src.core.config import settings
from src.db.models.task import User
from src.db.repositories import TaskRepository
from src.db.session import async_session_factory

logger = logging.getLogger(__name__)


async def check_reminders(bot: Bot) -> None:
    async with async_session_factory() as session:
        repo = TaskRepository(session)
        now = datetime.now(timezone.utc)
        tasks = await repo.due_for_reminder(now)

        for task in tasks:
            user = await session.get(User, task.user_id)
            if user is None:
                continue
            try:
                msg = await bot.send_message(
                    user.telegram_id,
                    texts.REMINDER.format(
                        task_id=task.id,
                        title=task.title,
                        due_at=task.due_at.astimezone().strftime("%d.%m.%Y %H:%M"),
                    ),
                    reply_markup=task_actions_kb(task),
                )

                # Пытаемся закрепить сообщение, но не падаем, если не вышло
                try:
                    await bot.pin_chat_message(
                        chat_id=user.telegram_id,
                        message_id=msg.message_id,
                        disable_notification=True,
                    )
                except Exception as pin_exc:  # noqa: BLE001
                    logger.warning(
                        "Не удалось закрепить напоминание для %s: %s",
                        user.telegram_id,
                        pin_exc,
                    )

                task.reminded_at = now

            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Не удалось отправить напоминание %s: %s",
                    user.telegram_id,
                    exc,
                )

        await session.commit()


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        check_reminders,
        "interval",
        seconds=settings.REMINDER_CHECK_INTERVAL,
        args=[bot],
        id="reminders",
        max_instances=1,
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Scheduler started (interval=%ss)", settings.REMINDER_CHECK_INTERVAL)
    return scheduler