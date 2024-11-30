from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig
from api.app.models import Base

# Настройка логирования
config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def include_object(object, name, type_, reflected, compare_to):
    # Исключаем spatial_ref_sys из миграций
    if name == "spatial_ref_sys":
        return False
    return True

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object  # Добавляем фильтр
        )
        with context.begin_transaction():
            context.run_migrations()

def run_migrations_offline():
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        include_object=include_object  # Добавляем фильтр
    )
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()