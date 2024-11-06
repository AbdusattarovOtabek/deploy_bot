from aiogram.fsm.state import StatesGroup, State

class Reg(StatesGroup):
    lang = State()


class AddHouseState(StatesGroup):
    name = State()
    price = State()
    area = State()
    rooms = State()
    location = State()
    description = State()
    images = State()  # Rasmlar uchun state


class AddCarState(StatesGroup):
    catalog = State()
    name = State()
    price = State()
    year = State()
    pozitsiya = State()
    color = State()
    oil = State()
    mileage = State()
    description = State()
    images = State()  # Rasmlar uchun state

