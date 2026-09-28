from datetime import datetime

from src.bot.handlers.tasks import _parse_manual_due


def test_parse_manual_due_full_format():
    """DD.MM.YYYY HH:MM парсится корректно."""
    dt = _parse_manual_due("25.12.2026 18:30")
    assert dt is not None
    # проверяем, что час/минута на месте (с учётом локальной TZ)
    assert dt.astimezone().strftime("%d.%m.%Y %H:%M") == "25.12.2026 18:30"


def test_parse_manual_due_short_format():
    """DD.MM HH:MM использует текущий год."""
    dt = _parse_manual_due("25.12 18:30")
    assert dt is not None
    assert dt.year == datetime.now().year


def test_parse_manual_due_invalid():
    """Мусор возвращает None."""
    assert _parse_manual_due("not a date") is None
    assert _parse_manual_due("") is None

def test_parse_manual_due_time_only_future():
    """HH:MM (будущее время сегодня) → сегодня."""
    from datetime import datetime, timedelta

    future = (datetime.now() + timedelta(hours=2)).strftime("%H:%M")
    dt = _parse_manual_due(future)
    assert dt is not None
    today = datetime.now().astimezone().date()
    assert dt.astimezone().date() == today


def test_parse_manual_due_time_only_past():
    """HH:MM (прошедшее время) → завтра."""
    from datetime import datetime, timedelta

    past = (datetime.now() - timedelta(hours=2)).strftime("%H:%M")
    dt = _parse_manual_due(past)
    assert dt is not None
    tomorrow = (datetime.now() + timedelta(days=1)).astimezone().date()
    assert dt.astimezone().date() == tomorrow