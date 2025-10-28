import asyncio
import datetime
import gspread
import toml
from oauth2client.service_account import ServiceAccountCredentials
from aiogram import Bot, Dispatcher
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
import pytz

# -------------------- Чтение конфигурации --------------------
config = toml.load("config.toml")
TOKEN = config["bot"]["token"]

# -------------------- Настройки бота --------------------
bot = Bot(token=TOKEN)
dp = Dispatcher()

# -------------------- Google Sheets авторизация --------------------
scope = ["https://spreadsheets.google.com/feeds",
         "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(
    "dailyplanner.json", scope
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
    tz = pytz.timezone("Europe/Moscow")
    today = datetime.datetime.now(tz).weekday()  # 0 = Monday
    return day_col[today]

def get_today_tasks():
    col = get_today_column()
    tasks_list = []
    rows = sheet.col_values(col)

    for i, task in enumerate(rows[2:], start=3):
        if not task.strip():
            continue

        done_value = sheet.cell(i, col+1).value
        if done_value and done_value.lower() == "true":
            continue

        tasks_list.append((i, task))
    
    return tasks_list

def build_keyboard(tasks):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=task, callback_data=f"done_{row}")]
        for row, task in tasks
    ])

# -------------------- Обработчик команды /start --------------------
@dp.message()
async def start_handler(message: Message):
    if message.text != "/start":
        return

    tasks = get_today_tasks()
    if not tasks:
        await message.answer("На сегодня задач нет 🎉")
        return

    keyboard = build_keyboard(tasks)
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

    await callback.answer("Задача выполнена ✅", show_alert=True)

    updated_tasks = [(r, t) for r, t in get_today_tasks() if r != row]

    if not updated_tasks:
        await callback.message.edit_text("Все задачи выполнены")
        return

    new_keyboard = build_keyboard(updated_tasks)
    await callback.message.edit_text("Ваши задачи на сегодня:", reply_markup=new_keyboard)


async def daily_task_sender():
    while True:
        now = datetime.datetime.now(pytz.timezone("Europe/Moscow"))
        target = now.replace(hour=2, minute=5, second=0, microsecond=0)

        if now>target:
            target += datetime.timedelta(days=1)

        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)

        user_id = config["bot"]["owner_id"]
        tasks = get_today_tasks()
        if not tasks:
            await bot.send_message(user_id, "На сегодня задач нет.")
        else:
            keyboard = build_keyboard(tasks)
            await bot.send_message(user_id, "Ваши задачи на сегодня", reply_markup=keyboard)

async def main():
    print("Bot started polling")
    asyncio.create_task(daily_task_sender())
    await dp.start_polling(bot)

# -------------------- Запуск бота --------------------
if __name__ == "__main__":
    asyncio.run(main())
