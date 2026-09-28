from datetime import date

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