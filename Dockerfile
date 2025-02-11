# Базовый образ с Python
FROM python:3.12.3-slim

# Установим рабочую директорию
WORKDIR /app

# Установка системных зависимостей
# RUN apt-get update && apt-get install -y \
#     build-essential \
#     libpq-dev \
#     && apt-get clean

# Установим Poetry
RUN pip install --no-cache-dir poetry

# # Скопируем только файлы, необходимые для установки зависимостей
COPY pyproject.toml poetry.lock /

# Установим зависимости без создания виртуального окружения
RUN poetry config virtualenvs.create false && poetry install  --no-root --no-dev

# Скопируем остальной код проекта
COPY . .

# Укажите команду запуска бота
CMD ["python", "main.py"]