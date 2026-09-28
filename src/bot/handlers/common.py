from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from src.bot import texts
from src.bot.keyboards.main_menu import main_menu
from src.services import TaskService

router = Router(name="common")


@router.message(CommandStart())
async def cmd_start(message: Message, session) -> None:
    service = TaskService(session)
    await service.register_user(
        message.from_user.id, message.from_user.username
    )
    await message.answer(
        texts.START.format(first_name=message.from_user.first_name),
        reply_markup=main_menu(),
    )

@router.message(F.text == "📖 Справка")
async def btn_help(message: Message) -> None:
    await cmd_help(message)


@router.message(F.text == "❌ Отмена")
async def btn_cancel(message: Message, state: FSMContext) -> None:
    await cmd_cancel(message, state)

@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    if current is None:
        await message.answer("Нечего отменять 🙂")
        return
    await state.clear()
    await message.answer("Отменено. Что дальше?")