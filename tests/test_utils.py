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