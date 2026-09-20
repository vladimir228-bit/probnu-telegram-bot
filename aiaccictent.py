import openpyxl
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncio
import os

# ====== НАСТРОЙКИ ======
TOKEN = os.getenv("7738471727:AAGjHMUW0s-K64VkShZ5XrVDHljW_cc-e80")  # ← ЗАМЕНИ НА СВОЙ ТОКЕН
BOT_NAME = "Aiaccictentbot"  # ← НАЗВАНИЕ БОТА

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====== СОСТОЯНИЯ ======
class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_phone = State()
    waiting_for_service = State()
    waiting_for_date = State()
    waiting_for_time = State()

# ====== УСЛУГИ ======
SERVICES = {
    "Мужская стрижка": 1000,
    "Детская стрижка": 800,
    "Стрижка машинкой": 500,
    "Стрижка + борода": 1500
}

TIME_SLOTS = ["10:00", "11:00", "12:00", "13:00", "14:00",
              "15:00", "16:00", "17:00", "18:00", "19:00"]

# ====== СОХРАНЕНИЕ В EXCEL ======
def save_to_excel(name, phone, service, date, time):
    filename = 'records.xlsx'

    if not os.path.exists(filename):
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["Имя", "Телефон", "Услуга", "Дата", "Время", "Цена"])
        wb.save(filename)

    wb = openpyxl.load_workbook(filename)
    ws = wb.active
    ws.append([name, phone, service, date, time, SERVICES[service]])
    wb.save(filename)

# ====== /start ======
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"💈 Добро пожаловать в {BOT_NAME}!\n\n"
        f"Для записи на стрижку используйте команду /record"
    )

# ====== /record ======
@dp.message(Command("record"))
async def cmd_record(message: types.Message, state: FSMContext):
    await message.answer("Введите ваше имя:")
    await state.set_state(Registration.waiting_for_name)

# ====== ИМЯ ======
@dp.message(Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите номер телефона:")
    await state.set_state(Registration.waiting_for_phone)

# ====== ТЕЛЕФОН ======
@dp.message(Registration.waiting_for_phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)

    services_text = "Выберите услугу (введите номер):\n"
    for i, service in enumerate(SERVICES.keys(), 1):
        services_text += f"{i}. {service} - {SERVICES[service]} руб.\n"

    await message.answer(services_text)
    await state.set_state(Registration.waiting_for_service)

# ====== УСЛУГА ======
@dp.message(Registration.waiting_for_service)
async def process_service(message: types.Message, state: FSMContext):
    try:
        service_num = int(message.text)
        service = list(SERVICES.keys())[service_num - 1]
        await state.update_data(service=service)

        await message.answer("Введите дату (ДД.ММ.ГГГГ):")
        await state.set_state(Registration.waiting_for_date)
    except:
        await message.answer("Пожалуйста, введите номер услуги цифрой")

# ====== ДАТА ======
@dp.message(Registration.waiting_for_date)
async def process_date(message: types.Message, state: FSMContext):
    await state.update_data(date=message.text)

    times = "\n".join(TIME_SLOTS)
    await message.answer(f"Выберите время:\n{times}")
    await state.set_state(Registration.waiting_for_time)

# ====== ВРЕМЯ ======
@dp.message(Registration.waiting_for_time)
async def process_time(message: types.Message, state: FSMContext):
    if message.text not in TIME_SLOTS:
        await message.answer("Это время недоступно. Выберите из списка:")
        return

    await state.update_data(time=message.text)
    data = await state.get_data()

    save_to_excel(
        data['name'],
        data['phone'],
        data['service'],
        data['date'],
        data['time']
    )

    await message.answer(
        f"✅ Запись подтверждена!\n\n"
        f"Имя: {data['name']}\n"
        f"Телефон: {data['phone']}\n"
        f"Услуга: {data['service']}\n"
        f"Дата: {data['date']}\n"
        f"Время: {data['time']}\n\n"
        f"Ждем вас в {BOT_NAME}!"
    )
    await state.clear()

# ====== ЗАПУСК ======
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())