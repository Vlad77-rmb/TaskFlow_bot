@pytest.mark.asyncio
async def test_create_task_with_explicit_due_at(session):
    from datetime import datetime, timezone
    dt = datetime(2026, 12, 25, 18, 30, tzinfo=timezone.utc)
    service = TaskService(session)
    task = await service.create_task(
        telegram_id=1, title="New Year", due_at=dt
    )
    assert task.due_at == dt