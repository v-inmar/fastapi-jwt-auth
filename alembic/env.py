import asyncio
from logging.config import fileConfig
from sqlalchemy import pool, create_engine
from sqlalchemy.engine import Connection
from alembic import context

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


from app.models.base import BaseModel
from app.models.user import AuthidModel, UserModel
from app.models.revoked_token import RevokedTokenModel
target_metadata = BaseModel.metadata

def run_migrations_offline() -> None:
    """Run migrations offline."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations online (SYNC engine)."""
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()
    
    connectable.dispose()

# ✅ Use SYNC online mode
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
