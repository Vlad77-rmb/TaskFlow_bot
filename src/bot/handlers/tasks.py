from datetime import date, datetime, time, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot import texts
from src.bot.keyboards import (
    PRIORITY_BY_CODE,
    month_kb,
    priority_emoji,
    priority_kb,
    skip_kb,
    task_actions_kb,
    time_kb,
)
from src.bot.states import TaskForm
from src.db.models.task import Priority, Task, TaskStatus
from src.services import TaskService

router = Router(name="tasks")


# ========== Утилиты ==========

def _format_task(task: Task) -> str:
    emoji = priority_emoji(task.priority)
    due = (
        f"\n⏰ до {task.due_at.astimezone():%d.%m.%Y %H:%M}"
        if task.due_at
        else ""
    )
    desc = f"\n📝 {task.description}" if task.description else ""
    return f"#{task.id} {emoji} <b>{task.title}</b>{desc}{due}"


def _parse_manual_due(raw: str) -> datetime | None:
    """Парсит 'DD.MM.YYYY HH:MM' или 'DD.MM HH:MM'. Возвращает aware-UTC."""
    raw = raw.strip()
    for fmt in ("%d.%m.%Y %H:%M", "%d.%m %H:%M"):
        try:
            dt = datetime.strptime(raw, fmt)
        except ValueError:
            continue
        if fmt == "%d.%m %H:%M":
            dt = dt.replace(year=date.today().year)
        # наивное время считаем локальным → в UTC
        return dt.astimezone().astimezone(timezone.utc)
    return None


# ========== /add ==========
@router.message(F.text == "➕ Новая задача")
async def btn_add(message: Message, state: FSMContext) -> None:
    await cmd_add(message, state)


@router.message(F.text == "📋 Мои задачи")
async def btn_list(message: Message, session) -> None:
    await cmd_list(message, session)

@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext) -> None:
    await state.set_state(TaskForm.title)
    await message.answer(texts.ASK_TITLE)


@router.message(TaskForm.title, F.text)
async def process_title(message: Message, state: FSMContext) -> None:
    title = message.text.strip()
    if not title:
        await message.answer(texts.TITLE_EMPTY)
        return
    await state.update_data(title=title)
    await state.set_state(TaskForm.description)
    await message.answer(texts.ASK_DESCRIPTION, reply_markup=skip_kb())


# ========== Описание ==========

@router.callback_query(TaskForm.description, F.data == "skip")
async def skip_description(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(description=None)
    await _ask_due(callback, state)
    await callback.answer()


@router.message(TaskForm.description, F.text)
async def process_description(message: Message, state: FSMContext) -> None:
    await state.update_data(description=message.text.strip())
    await _ask_due(message, state)


async def _ask_due(event, state: FSMContext) -> None:
    """Показать календарь на текущий месяц."""
    await state.set_state(TaskForm.due_at)
    today = date.today()
    kb = month_kb(today.year, today.month, today=today)
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(texts.ASK_DUE, reply_markup=kb)
    else:
        await event.answer(texts.ASK_DUE, reply_markup=kb)


# ========== Календарь ==========
@router.callback_query(TaskForm.due_at, F.data == "cal:past")
async def cal_past(callback: CallbackQuery) -> None:
    await callback.answer(
        "Нельзя использовать прошедшую дату. Выберите актуальную дату.",
        show_alert=True,
    )


@router.callback_query(TaskForm.due_at, F.data == "cal:ignore")
async def cal_ignore(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(TaskForm.due_at, F.data.startswith("cal:nav:"))
async def cal_nav(callback: CallbackQuery) -> None:
    _, _, ym = callback.data.split(":")
    year, month = map(int, ym.split("-"))
    today = date.today()
    await callback.message.edit_reply_markup(
        reply_markup=month_kb(year, month, today=today)
    )
    await callback.answer()


@router.callback_query(TaskForm.due_at, F.data == "cal:back")
async def cal_back(callback: CallbackQuery) -> None:
    today = date.today()
    await callback.message.edit_text(
        texts.ASK_DUE,
        reply_markup=month_kb(today.year, today.month, today=today),
    )
    await callback.answer()


@router.callback_query(TaskForm.due_at, F.data == "cal:skip")
async def cal_skip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.update_data(due_at=None)
    await state.set_state(TaskForm.confirm)
    await callback.message.edit_text(
        texts.ASK_PRIORITY, reply_markup=priority_kb()
    )
    await callback.answer()


@router.callback_query(TaskForm.due_at, F.data.startswith("cal:day:"))
async def cal_day(callback: CallbackQuery) -> None:
    _, _, iso = callback.data.split(":")
    day = date.fromisoformat(iso)
    await callback.message.edit_text(
        texts.CALENDAR_TIME_TITLE, reply_markup=time_kb(day)
    )
    await callback.answer()


@router.callback_query(TaskForm.due_at, F.data.startswith("cal:time:"))
async def cal_time(callback: CallbackQuery, state: FSMContext) -> None:
    _, _, iso, hhmm = callback.data.split(":", 3)
    day = date.fromisoformat(iso)
    hour, minute = map(int, hhmm.split(":"))
    # локальное время → UTC aware
    local_dt = datetime.combine(day, time(hour, minute)).astimezone()
    if local_dt < datetime.now().astimezone():
        await callback.answer(
            "Нельзя ставить задачу на прошедшее время.",
            show_alert=True,
        )
        return
    utc_dt = local_dt.astimezone(timezone.utc)
    await state.update_data(due_at=utc_dt.isoformat())
    await state.set_state(TaskForm.confirm)
    await callback.message.edit_text(
        f"{texts.CALENDAR_DONE.format(dt=local_dt.strftime('%d.%m.%Y %H:%M'))}\n\n"
        f"{texts.ASK_PRIORITY}",
        reply_markup=priority_kb(),
    )
    await callback.answer()


@router.callback_query(TaskForm.due_at, F.data == "cal:manual")
async def cal_manual(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(TaskForm.due_manual)
    await callback.message.edit_text(
        "✏️ Введи дату и время в формате <code>ДД.ММ.ГГГГ ЧЧ:ММ</code>\n"
        "Например: <code>25.12.2026 18:30</code>"
    )
    await callback.answer()


@router.message(TaskForm.due_manual, F.text)
async def process_manual_due(message: Message, state: FSMContext) -> None:
    dt = _parse_manual_due(message.text)
    if dt is None:
        await message.answer(texts.DUE_INVALID)
        return
    await state.update_data(due_at=dt.isoformat())
    await state.set_state(TaskForm.confirm)
    await message.answer(texts.ASK_PRIORITY, reply_markup=priority_kb())


# ========== Приоритет и создание ==========

@router.callback_query(TaskForm.confirm, F.data.startswith("prio:"))
async def process_priority(
    callback: CallbackQuery, state: FSMContext, session
) -> None:
    code = callback.data.split(":")[1]
    priority = PRIORITY_BY_CODE[code]
    data = await state.get_data()
    await state.clear()

    service = TaskService(session)
    due_at_str = data.get("due_at")
    due_at = datetime.fromisoformat(due_at_str) if due_at_str else None

    task = await service.create_task(
        telegram_id=callback.from_user.id,
        title=data["title"],
        description=data.get("description"),
        priority=priority,
        due_at=due_at,
    )
    

    template = texts.TASK_CREATED if task.due_at else texts.TASK_CREATED_NO_DUE
    await callback.message.edit_text(template.format(task=_format_task(task)))
    await callback.answer("Готово ✅")


# ========== /list, /done, /delete ==========

@router.message(Command("list"))
async def cmd_list(message: Message, session) -> None:
    service = TaskService(session)
    tasks = await service.list_tasks(message.from_user.id, TaskStatus.TODO)
    if not tasks:
        await message.answer(texts.EMPTY_LIST)
        return

    await message.answer(texts.ACTIVE_TASKS_HEADER)
    for task in tasks:
        await message.answer(
            _format_task(task), reply_markup=task_actions_kb(task)
        )


@router.message(Command("done"))
async def cmd_done(message: Message, session) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].isdigit():
        await message.answer(texts.USAGE_DONE)
        return

    service = TaskService(session)
    task = await service.complete_task(message.from_user.id, int(args[1]))
    if task is None:
        await message.answer(texts.TASK_NOT_FOUND)
        return
    await message.answer(texts.TASK_DONE.format(task_id=task.id))


@router.message(Command("delete"))
async def cmd_delete(message: Message, session) -> None:
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].isdigit():
        await message.answer(texts.USAGE_DELETE)
        return

    service = TaskService(session)
    ok = await service.delete_task(message.from_user.id, int(args[1]))
    await message.answer(
        texts.TASK_DELETED.format(task_id=args[1]) if ok else texts.TASK_NOT_FOUND
    )


@router.callback_query(F.data.startswith("task:"))
async def task_action(callback: CallbackQuery, session) -> None:
    _, action, task_id_str = callback.data.split(":")
    task_id = int(task_id_str)
    service = TaskService(session)

    if action == "done":
        task = await service.complete_task(callback.from_user.id, task_id)
        if task is None:
            await callback.answer(texts.TASK_NOT_FOUND, show_alert=True)
            return

        # ← открепляем сообщение (если оно было закреплено)
        try:
            await callback.bot.unpin_chat_message(
                chat_id=callback.from_user.id,
                message_id=callback.message.message_id,
            )
        except Exception:
            pass

        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(texts.TASK_DONE.format(task_id=task_id))

    elif action == "delete":
        ok = await service.delete_task(callback.from_user.id, task_id)
        if not ok:
            await callback.answer(texts.TASK_NOT_FOUND, show_alert=True)
            return

        # ← открепляем
        try:
            await callback.bot.unpin_chat_message(
                chat_id=callback.from_user.id,
                message_id=callback.message.message_id,
            )
        except Exception:
            pass

        await callback.message.edit_reply_markup(reply_markup=None)
        await callback.message.answer(texts.TASK_DELETED.format(task_id=task_id))

    await callback.answer()