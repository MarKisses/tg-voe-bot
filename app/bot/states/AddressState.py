from aiogram.fsm.state import State, StatesGroup


class AddressState(StatesGroup):
    choosing_city = State()
    choosing_street = State()
    choosing_house = State()
    ready = State()