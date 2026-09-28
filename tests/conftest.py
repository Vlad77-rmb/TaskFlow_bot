from datetime import date
import pytest_asyncio
from src.bot.keyboards import month_kb, time_kb


def test_month_kb_has_nav_buttons():
    kb = month_kb(2026, 10, today=date(2026, 10, 15))
    all_callbacks = [b.callback_data for row in kb.inline_keyboard for b in row]
    assert "cal:nav:2026-09" in all_callbacks
    assert "cal:nav:2026-11" in all_callbacks
    assert "cal:day:2026-10-20" in all_callbacks


def test_time_kb_has_slots():
    kb = time_kb(date(2026, 10, 20))
    all_callbacks = [b.callback_data for row in kb.inline_keyboard for b in row]
    assert "cal:time:2026-10-20:09:00" in all_callbacks
    assert "cal:time:2026-10-20:23:30" in all_callbacks

    import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.db.models import Base


@pytest_asyncio.fixture
async def session() -> AsyncSession:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as s:
        yield s

    await engine.dispose()