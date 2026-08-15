"""
sqlalchemy:名字sql log 幂
作用：通过声明式方式让Python语言操作数据库（MySQL PGSQL...）
使用：1. （声明）定义数据模型 2. 利用session对象通过API方式来交互数据库（crud）

操作自己的数据库（customer_service） dialogue_states表（整个对话状态：聚合根）

"""
import asyncio

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from atguigu.config.config import settings


db_engine: AsyncEngine | None = None
session_factory: async_sessionmaker[AsyncSession] | None = None

def init_db_engine():
    global db_engine,session_factory

    db_engine = create_async_engine(url = settings.database_url,echo = True)
    session_factory = async_sessionmaker(db_engine,expire_on_commit=False)

async def dispose_db_engine():
    await db_engine.dispose()


async def main_test():
    init_db_engine()

    async with session_factory() as session:
        result = await session.execute(text("select 1"))
        raw = result.mappings().fetchone()  # fetchone  # (1,)   mappings:{'1': 1}
        print(raw)

    await dispose_db_engine()

if __name__ == '__main__':
    asyncio.run(main_test())




