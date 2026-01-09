import os
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

def run_migrations(target_metadata):
    """
    Standard migration runner for all services.
    Reads DATABASE_URL from environment.
    """
    config = context.config

    # Interpret the config file for Python logging.
    if config.config_file_name is not None:
        fileConfig(config.config_file_name)

    def get_url():
        url = os.getenv("DATABASE_URL")
        if not url:
            raise ValueError("DATABASE_URL environment variable is not set")
        return url

    def run_migrations_offline() -> None:
        """Run migrations in 'offline' mode."""
        url = get_url()
        context.configure(
            url=url,
            target_metadata=target_metadata,
            literal_binds=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()

    def run_migrations_online() -> None:
        """Run migrations in 'online' mode."""
        # Get the alembic section from alembic.ini
        configuration = config.get_section(config.config_ini_section)
        if configuration is None:
            configuration = {}
        
        # Override the sqlalchemy.url with the environment variable
        configuration["sqlalchemy.url"] = get_url()
        
        connectable = engine_from_config(
            configuration,
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        with connectable.connect() as connection:
            context.configure(
                connection=connection, target_metadata=target_metadata
            )

            with context.begin_transaction():
                context.run_migrations()

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()
