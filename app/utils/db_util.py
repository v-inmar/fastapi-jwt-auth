from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import get_config

engine = create_async_engine(
    get_config().DATABASE_URL, 
    echo=False,  # TODO: False on prod
    future=True
)


AsyncSessionLocal = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)


# async def get_session() -> AsyncGenerator[AsyncSession, None]:
#     async with AsyncSessionLocal() as session:
#         yield session


async def get_transaction_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        async with session.begin():  # Auto transaction per request
            try:
                yield session
            except:
                await session.rollback()
                raise
            # Auto-commits on exit
