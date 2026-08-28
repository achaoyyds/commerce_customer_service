import asyncio
from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine,AsyncConnection,async_sessionmaker,AsyncEngine
from sqlalchemy import text
from atuguigu.config.settings import settings

session_engine: AsyncEngine | None = None
session_factory : async_sessionmaker[AsyncSession] | None = None

def init_db_engine():
    global session_engine
    global session_factory

    session_engine = create_async_engine(url = settings.database_url,echo = True)
    session_factory = async_sessionmaker(session_engine,expire_on_commit=False)


async def dispose_engine():
    await session_engine.dispose()


async def main_test():

    init_db_engine()

    async with session_factory() as session:
        result_cursor = await  session.execute(text("select now() as now_time"))
        print(result_cursor.mappings().fetchone())
        cursor = await session.execute(text("select 1"))  # CursorResult
        print(cursor.mappings().fetchone())

    await dispose_engine()

if __name__ == '__main__':
    asyncio.run(main_test())




