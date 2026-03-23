from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool

# Import all models so Alembic can detect them for autogenerate
import models.customer
import models.job
import models.order
import models.product
import models.stock_projection
import models.user  # noqa: F401
from alembic import context
from core.config import settings
from core.database import Base

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    # Generates SQL without a live DB connection — useful for reviewing changes
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        include_schemas=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_schemas=True,
            # Tells autogenerate to look inside our custom schemas, not just public
            include_object=lambda obj, name, type_, reflected, compare_to: (
                getattr(obj, "schema", None) in (None, "customers", "sales", "inventory", "auth", "workers")
                if type_ == "table"
                else True
            ),
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
