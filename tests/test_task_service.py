from datetime import UTC, datetime

import pytest

from src.db.models.task import Priority, TaskStatus
from src.services.task_service import TaskService


@pytest.mark.asyncio
async def test_create_task_minimal(session):
    """Задача создаётся с дефолтными значениями."""
    service = TaskService(session)
    task = await service.create_task(telegram_id=100, title="Buy milk")

    assert task.id is not None
    assert task.title == "Buy milk"
    assert task.priority == Priority.MEDIUM
    assert task.status == TaskStatus.TODO
    assert task.due_at is None


@pytest.mark.asyncio
async def test_create_task_with_priority(session):
    """Приоритет сохраняется."""
    service = TaskService(session)
    task = await service.create_task(
        telegram_id=100, title="Urgent", priority=Priority.HIGH
    )
    assert task.priority == Priority.HIGH


@pytest.mark.asyncio
async def test_create_task_with_due_in_minutes(session):
    """due_in_minutes конвертируется в due_at."""
    service = TaskService(session)
    before = datetime.now(UTC)
    task = await service.create_task(
        telegram_id=100, title="Soon", due_in_minutes=30
    )
    assert task.due_at is not None
    delta = (task.due_at - before).total_seconds()
    assert 29 * 60 < delta < 31 * 60


@pytest.mark.asyncio
async def test_list_tasks_only_own(session):
    """Пользователь видит только свои задачи."""
    service = TaskService(session)
    await service.create_task(telegram_id=1, title="Task of user 1")
    await service.create_task(telegram_id=2, title="Task of user 2")

    tasks = await service.list_tasks(1, TaskStatus.TODO)
    assert len(tasks) == 1
    assert tasks[0].title == "Task of user 1"


@pytest.mark.asyncio
async def test_complete_task(session):
    """Задача помечается выполненной."""
    service = TaskService(session)
    task = await service.create_task(telegram_id=1, title="Do it")

    done = await service.complete_task(1, task.id)
    assert done is not None
    assert done.status == TaskStatus.DONE


@pytest.mark.asyncio
async def test_complete_nonexistent_task(session):
    """Завершение несуществующей задачи — None."""
    service = TaskService(session)
    result = await service.complete_task(1, 9999)
    assert result is None


@pytest.mark.asyncio
async def test_delete_task(session):
    """Удаление задачи."""
    service = TaskService(session)
    task = await service.create_task(telegram_id=1, title="Delete me")
    ok = await service.delete_task(1, task.id)
    assert ok is True
    assert await service.list_tasks(1, TaskStatus.TODO) == []


@pytest.mark.asyncio
async def test_delete_foreign_task(session):
    """Нельзя удалить чужую задачу."""
    service = TaskService(session)
    task = await service.create_task(telegram_id=1, title="Mine")
    ok = await service.delete_task(2, task.id)  # другой пользователь
    assert ok is False


@pytest.mark.asyncio
async def test_list_filters_by_status(session):
    """list_tasks фильтрует по статусу."""
    service = TaskService(session)
    t1 = await service.create_task(telegram_id=1, title="A")
    await service.create_task(telegram_id=1, title="B")
    await service.complete_task(1, t1.id)

    todo = await service.list_tasks(1, TaskStatus.TODO)
    done = await service.list_tasks(1, TaskStatus.DONE)
    assert len(todo) == 1
    assert len(done) == 1

@pytest.mark.asyncio
async def test_create_task_with_explicit_due_at(session):
    from datetime import datetime
    dt = datetime(2026, 12, 25, 18, 30, tzinfo=UTC)
    service = TaskService(session)
    task = await service.create_task(
        telegram_id=1, title="New Year", due_at=dt
    )
    assert task.due_at == dt
