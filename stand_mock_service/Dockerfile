# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем рабочую директорию внутри контейнера
WORKDIR /app

# Копируем файл с зависимостями
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы приложения в рабочую директорию
COPY ./app .

# Указываем команду, которая будет выполняться при запуске контейнера
# Аргументы будут передаваться через docker-compose
ENTRYPOINT ["python", "main.py"]