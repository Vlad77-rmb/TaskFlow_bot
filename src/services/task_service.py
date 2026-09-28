from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.task import Priority, Task, TaskStatus, User
from src.db.repositories import TaskRepository, UserRepository


class TaskService:
    """Бизнес-логика. Хендлеры зависят только от этого класса."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.users = UserRepository(session)
        self.tasks = TaskRepository(session)

    async def register_user(
        self, telegram_id: int, username: str | None
    ) -> User:
        user = await self.users.get_or_create(telegram_id, username)
        await self.session.commit()
        return user

    async def create_task(
        self,
        telegram_id: int,
        title: str,
        description: str | None = None,
        priority: Priority = Priority.MEDIUM,
        due_in_minutes: int | None = None,
        due_at: datetime | None = None,
    ) -> Task:
        user = await self.users.get_or_create(telegram_id)

        if due_at is None and due_in_minutes is not None:
            due_at = datetime.now(UTC) + timedelta(minutes=due_in_minutes)

        task = await self.tasks.create(
            user_id=user.id,
            title=title,
            description=description,
            priority=priority,
            due_at=due_at,
        )
        await self.session.commit()
        return task

    async def list_tasks(
        self, telegram_id: int, status: TaskStatus | None = None
    ) -> list[Task]:
        user = await self.users.get_or_create(telegram_id)
        return await self.tasks.list_for_user(user.id, status)

    async def get_task(self, telegram_id: int, task_id: int) -> Task | None:
        user = await self.users.get_or_create(telegram_id)
        return await self.tasks.get(task_id, user.id)

    async def complete_task(
        self, telegram_id: int, task_id: int
    ) -> Task | None:
        task = await self.get_task(telegram_id, task_id)
        if task is None:
            return None
        await self.tasks.update(task, status=TaskStatus.DONE)
        await self.session.commit()
        return task

    async def delete_task(
        self, telegram_id: int, task_id: int
    ) -> bool:
        task = await self.get_task(telegram_id, task_id)
        if task is None:
            return False
        await self.tasks.delete(task)
        await self.session.commit()
        return True