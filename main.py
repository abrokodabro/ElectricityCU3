import asyncio
import os
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
import asyncpg
import pandas as pd

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить СИЗ")],
        [KeyboardButton(text="📋 Список")],
        [KeyboardButton(text="📊 Excel отчет")]
    ],
    resize_keyboard=True
)

async def get_conn():
    return await asyncpg.connect(DATABASE_URL)

@dp.message()
async def handler(message: types.Message):
    if message.text == "/start":
        await message.answer("Система учета СИЗ", reply_markup=menu)

    elif message.text == "📋 Список":
        conn = await get_conn()
        rows = await conn.fetch("SELECT name, expiry_date FROM siz")

        if not rows:
            await message.answer("Список пуст")
            return

        text = ""
        for r in rows:
            text += f"{r['name']} — до {r['expiry_date']}\n"

        await message.answer(text)

    elif message.text == "📊 Excel отчет":
        conn = await get_conn()
        rows = await conn.fetch("SELECT name, test_date, expiry_date FROM siz")

        data = [dict(r) for r in rows]
        df = pd.DataFrame(data)

        file = "report.xlsx"
        df.to_excel(file, index=False)

        await message.answer_document(types.FSInputFile(file))

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
