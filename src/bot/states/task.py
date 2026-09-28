from aiogram.fsm.state import State, StatesGroup


class TaskForm(StatesGroup):
    title = State()
    description = State()
    due_at = State()
    due_manual = State()  
    confirm = State()