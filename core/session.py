from contextlib import asynccontextmanager, contextmanager
from typing import Generator, AsyncGenerator
import asyncio
from sqlalchemy import Sequence, text, create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, create_session, sessionmaker

# from sqlalchemy.orm import sessionmaker
from core.config import settings


serial_seq = Sequence('serial_number_seq', start=1, increment=1)  # Create a sequence

if settings.DB_URL is None:
    raise ValueError("DB_URL environment variable is not found")


# engine = create_async_engine(settings.DB_URL, future=True, echo=True)
# async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
engine = create_engine(settings.DB_URL, future=True, echo=False)
session_maker = sessionmaker(engine, expire_on_commit=False, autocommit=False, autoflush=False)
# loop = asyncio.get_event_loop_policy().get_event_loop()


@asynccontextmanager
async def create_sequence():
    """Ensure the sequence exists before creating tables."""

    @contextmanager
    def get_session():
        with session_maker() as session:
            yield session  # Ensure session is properly yielded
            session.close()

    with get_session() as session:
        with session.begin():  # ✅ Use session.begin() inside an async session
            session.execute(
                text("CREATE SEQUENCE IF NOT EXISTS serial_number_seq START 1 INCREMENT 1;")
            )
    yield


# # Run the async setup
# asyncio.run(create_sequence())


# async def get_db():
#     session: AsyncSession = async_session_maker()
#     try:
#         yield session
#     finally:
#         await session.close()



async def get_db() -> Session:
    with session_maker() as session:
        yield session  # Ensure session is properly yielded
        session.close()



def connection(method):
    async def wrapper(*args, **kwargs):
        async with session_maker() as session:
            try:
                # Явно не открываем транзакции, так как они уже есть в контексте
                return await method(*args, session=session, **kwargs)
            except Exception as e:
                await session.rollback()  # Откатываем сессию при ошибке
                raise e  # Поднимаем исключение дальше
            finally:
                await session.close()  # Закрываем сессию

    return wrapper

