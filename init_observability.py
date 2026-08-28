"""初始化可观测性三张表（幂等：已存在则跳过）。

用法：uv run init_observability.py
创建：dialogue_message（拆历史消息） / dialogue_session（会话汇总） / dialogue_turn（轮次 trace）
"""
import asyncio
import sys

from atuguigu.infrastructure import db_client
from atuguigu.observability.models import DialogueMessage, DialogueSession, DialogueTurn
from atuguigu.repository.base import Base


async def main():
    db_client.init_db_engine()
    tables = [DialogueMessage.__table__, DialogueSession.__table__, DialogueTurn.__table__]
    async with db_client.session_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all, tables=tables)
        print("可观测性表创建完成：dialogue_message / dialogue_session / dialogue_turn")
    await db_client.dispose_engine()


if __name__ == "__main__":
    asyncio.run(main())
    sys.exit(0)