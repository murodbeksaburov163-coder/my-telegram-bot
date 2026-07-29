from aiogram.fsm.state import StatesGroup, State


class AddChannel(StatesGroup):
    waiting_forward = State()


class StartBattle(StatesGroup):
    waiting_prize = State()
    waiting_end_time = State()


class SettingsFSM(StatesGroup):
    waiting_value = State()
