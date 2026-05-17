import sys
import asyncio
from os.path import abspath, dirname
import os

# Добавляем путь к приложению
sys.path.insert(0, abspath(dirname(dirname(__file__))))

from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config  # Импортируем асинхронный движок
from alembic import context

from app.core.config import settings
from app.db.models import *
from app.db.base import Base

# Объект конфигурации Alembic
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = settings.DATABASE_URL
    context.configure(
        url=str(url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

# Вспомогательная функция для запуска миграций в синхронном стиле внутри асинхронного соединения
def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()

async def run_migrations_online() -> None:
    """Запуск миграций в асинхронном режиме"""
    
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = str(settings.DATABASE_URL)

    # Создаем асинхронный движок
    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        # Alembic внутри синхронный, поэтому мы используем run_sync
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

if context.is_offline_mode():
    run_migrations_offline()
else:
    # Запускаем асинхронную функцию
    asyncio.run(run_migrations_online())