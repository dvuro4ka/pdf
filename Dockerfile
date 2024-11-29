# Используем slim-образ Python версии 3.11.4
FROM python:3.11.4-slim

# Устанавливаем необходимые системные зависимости
RUN apt-get update && apt-get install -y \
    libimage-exiftool-perl \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY . /app

# Создаём папку check для сохранения файлов
RUN mkdir /app/check

# Устанавливаем зависимости проекта из requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Устанавливаем переменные окружения (например, токен)

# Запускаем приложение (укажи точку входа, если необходимо)

CMD ["python", "bot.py"]