# Используем официальный образ Python 3.12
FROM python:3.12-slim

WORKDIR /app

# Копируем проект
COPY . /app

# Обновляем pip и устанавливаем uv и git
RUN apt update && apt install -y git \
    && pip install --upgrade pip \
    && pip install uv

# Устанавливаем зависимости через uv
# Это создаст виртуальное окружение uv и установит всё, что нужно
RUN uv run pip install .

# Копируем конфиг и JSON ключи
COPY config.toml /app/config.toml
COPY dailyplanner.json /app/dailyplanner.json

# Запуск бота
CMD ["python", "main.py"]

