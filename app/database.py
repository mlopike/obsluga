from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase


from config import Settings

settings = Settings()

engine = create_async_engine(
    str(settings.db_url),
    echo = True
)

async_session = async_sessionmaker(
    expire_on_commit=False,
    bind=engine,
    class_=AsyncSession
)
