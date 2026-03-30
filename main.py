import asyncio
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
import asyncpg
import pandas as pd

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- Состояния ---
class AddSIZ(StatesGroup):
    name = State()
    test_date = State()
    expiry_date = State()
    description = State()

# --- Кнопки ---
menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить СИЗ")],
        [KeyboardButton(text="📋 Список")],
        [KeyboardButton(text="📊 Excel отчет")]
    ],
    resize_keyboard=True
)

# --- БД ---
async def get_conn():
    return await asyncpg.connect(DATABASE_URL)

# --- Старт ---
@dp.message(F.text == "/start")
async def start(message: types.Message):
    await message.answer("Система учета СИЗ", reply_markup=menu)

# --- Добавление ---
@dp.message(F.text == "➕ Добавить СИЗ")
async def add_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название СИЗ:")
    await state.set_state(AddSIZ.name)

@dp.message(AddSIZ.name)
async def add_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите дату испытания (ГГГГ-ММ-ДД):")
    await state.set_state(AddSIZ.test_date)

@dp.message(AddSIZ.test_date)
async def add_test_date(message: types.Message, state: FSMContext):
    await state.update_data(test_date=message.text)
    await message.answer("Введите срок окончания (ГГГГ-ММ-ДД):")
    await state.set_state(AddSIZ.expiry_date)

@dp.message(AddSIZ.expiry_date)
async def add_expiry(message: types.Message, state: FSMContext):
    await state.update_data(expiry_date=message.text)
    await message.answer("Введите описание:")
    await state.set_state(AddSIZ.description)

@dp.message(AddSIZ.description)
async def add_description(message: types.Message, state: FSMContext):
    data = await state.get_data()

    conn = await get_conn()

    await conn.execute("""
        INSERT INTO siz (name, test_date, expiry_date, description)
        VALUES ($1, $2, $3, $4)
    """,
    data["name"],
    data["test_date"],
    data["expiry_date"],
    message.text
    )

    await message.answer("✅ СИЗ добавлен", reply_markup=menu)
    await state.clear()

# --- Список ---
@dp.message(F.text == "📋 Список")
async def list_siz(message: types.Message):
    conn = await get_conn()
    rows = await conn.fetch("SELECT name, expiry_date FROM siz")

    if not rows:
        await message.answer("Список пуст")
        return

    text = ""
    for r in rows:
        text += f"{r['name']} — до {r['expiry_date']}\n"

    await message.answer(text)

# --- Excel ---
@dp.message(F.text == "📊 Excel отчет")
async def excel(message: types.Message):
    conn = await get_conn()
    rows = await conn.fetch("SELECT name, test_date, expiry_date FROM siz")

    data = [dict(r) for r in rows]
    df = pd.DataFrame(data)

    file = "report.xlsx"
    df.to_excel(file, index=False)

    await message.answer_document(types.FSInputFile(file))

# --- Запуск ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())