from server.config import Settings
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# import databases
# import sqlalchemy
# from sqlalchemy import create_engine

# from server.config import Settings

# database = databases.Database(Settings().DATABASE_URL_ASYNC)

# engine = create_engine(Settings().DATABASE_URL_ASYNC)

# metadata = sqlalchemy.MetaData(bind=engine)


# DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(Settings().DATABASE_URL, future=True, echo=True)
async_session = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()  # model base class


# async def init_db():
#     import models

#     async with engine.begin() as conn:
#         await conn.run_sync(models.Base.metadata.create_all)


async def get_session():
    async with async_session() as session:
        yield session


async def init_db():
    async with engine.begin() as conn:
        # Use run_sync to call create_all in a synchronous manner
        await conn.run_sync(Base.metadata.create_all)
