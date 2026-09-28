from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models.task import Priority, Task, TaskStatus


class TaskRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: int,
        title: str,
        description: str | None = None,
        priority: Priority = Priority.MEDIUM,
        due_at: datetime | None = None,
    ) -> Task:
        task = Task(
            user_id=user_id,
            title=title,
            description=description,
            priority=priority,
            due_at=due_at,
        )
        self.session.add(task)
        await self.session.flush()
        return task

    async def get(self, task_id: int, user_id: int) -> Task | None:
        stmt = select(Task).where(Task.id == task_id, Task.user_id == user_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list_for_user(
        self, user_id: int, status: TaskStatus | None = None
    ) -> list[Task]:
        stmt = select(Task).where(Task.user_id == user_id)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        stmt = stmt.order_by(
            Task.due_at.asc().nulls_last(),
            Task.created_at.desc(),
        )
        return list((await self.session.execute(stmt)).scalars().all())

    async def update(self, task: Task, **fields) -> Task:
        for key, value in fields.items():
            setattr(task, key, value)
        await self.session.flush()
        return task

    async def delete(self, task: Task) -> None:
        await self.session.delete(task)
        await self.session.flush()

    async def due_for_reminder(self, now: datetime) -> list[Task]:
        stmt = select(Task).where(
            Task.status == TaskStatus.TODO,
            Task.due_at.is_not(None),
            Task.due_at <= now,
            Task.reminded_at.is_(None),
        )
        return list((await self.session.execute(stmt)).scalars().all())