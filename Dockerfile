# Используем slim-образ для уменьшения размера
FROM python:3.11-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Обновляем пакеты и ставим системные зависимости, которые нужны нашим Python-библиотекам
# postgresql-client нужен для утилиты pg_isready
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Копируем только файл с зависимостями, чтобы кэшировать этот слой
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt


# Копируем конфигурацию Alembic и сами миграции
COPY alembic.ini .
COPY alembic ./alembic


# Копируем остальной код приложения. 
# При разработке эта папка будет "перекрыта" volume-ом, но для production-сборки это необходимо.
COPY ./app ./app

# Команда по умолчанию, которую мы будем переопределять в docker-compose.
# Она нужна, если кто-то захочет запустить контейнер командой `docker run`.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8008"]