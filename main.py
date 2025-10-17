import asyncio
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# -------------------- Настройки бота --------------------
TOKEN = "8493460424:AAHn3RYrdevCssLtvqwU4X_XxbQ8BITZD_0"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# -------------------- Google Sheets авторизация --------------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "dailyplanner-475406-c4c53085245d.json", scope
)
client = gspread.authorize(creds)
sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1pReZ9Vl7AzOIwb-vLBf87R6BzHy1TkBz4wDkFLwZPUg/edit"
).sheet1

# -------------------- Соответствие дней недели колонкам --------------------
day_col = {
    0: 2,   # Понедельник -> колонка B
    1: 4,   # Вторник -> колонка D
    2: 6,   # Среда -> колонка F
    3: 8,   # Четверг -> колонка H
    4: 10,  # Пятница -> колонка J
    5: 12,  # Суббота -> колонка L
    6: 14,  # Воскресенье -> колонка N
}

def get_today_column():
    today = datetime.datetime.today().weekday()  # 0 = Monday
    return day_col[today]

# -------------------- Обработчик команды /start --------------------
@dp.message()
async def start_handler(message: Message):
    if message.text != "/start":
        return

    col = get_today_column()
    tasks = sheet.col_values(col)[1:]  # пропускаем заголовок

    # Убираем пустые строки
    tasks = [(i + 2, task) for i, task in enumerate(tasks) if task.strip()]

    if not tasks:
        await message.answer("На сегодня задач нет 🎉")
        return

    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=task, callback_data=f"done_{row_index}")]
        for row_index, task in tasks
    ])

    await message.answer("Ваши задачи на сегодня:", reply_markup=keyboard)

# -------------------- Обработчик нажатий на кнопки --------------------
@dp.callback_query()
async def mark_done_callback(callback: CallbackQuery):
    if not callback.data.startswith("done_"):
        return

    row = int(callback.data.split("_")[1])
    col = get_today_column()

    # Ставим ✅ в соседней колонке
    sheet.update_cell(row, col + 1, "true")

    # Получаем текст задачи
    task_text = sheet.cell(row, col).value

    await callback.answer("Задача выполнена ✅")
    await bot.send_message(callback.from_user.id, f"✅ Задача выполнена: {task_text}")

# -------------------- Запуск бота --------------------
if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))

