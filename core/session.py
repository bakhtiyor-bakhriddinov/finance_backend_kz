from typing import Generator, AsyncGenerator
import asyncio
from sqlalchemy import Sequence
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
# from sqlalchemy.orm import sessionmaker
from core.config import settings


serial_seq = Sequence('serial_number_seq', start=1, increment=1)  # Create a sequence

if settings.DB_URL is None:
    raise ValueError("DB_URL environment variable is not found")


engine = create_async_engine(settings.DB_URL, future=True, echo=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


async def create_sequence():
    """Ensure the sequence exists before creating tables."""
    async with async_session_maker() as session:
        async with session.begin():  # ✅ Use session.begin() inside an async session
            await session.execute(
                "CREATE SEQUENCE IF NOT EXISTS serial_number_seq START 1 INCREMENT 1;"
            )


# # Run the async setup
# asyncio.run(create_sequence())


async def get_db():
    session: AsyncSession = async_session_maker()
    try:
        yield session
    finally:
        await session.close()



def connection(method):
    async def wrapper(*args, **kwargs):
        async with async_session_maker() as session:
            try:
                # Явно не открываем транзакции, так как они уже есть в контексте
                return await method(*args, session=session, **kwargs)
            except Exception as e:
                await session.rollback()  # Откатываем сессию при ошибке
                raise e  # Поднимаем исключение дальше
            finally:
                await session.close()  # Закрываем сессию

    return wrapper

