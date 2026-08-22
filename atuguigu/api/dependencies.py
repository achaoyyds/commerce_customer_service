"""
管理service.
FASTAPI的依赖注入：Depends
Annotated；注解。可以将类型提示和依赖注入绑定在一起
"""
from typing import Annotated
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from atuguigu.engines.dialogue_engine import DialogueEngine
from atuguigu.repository.dialogue_repository import DialogueRepository
from atuguigu.services.dialogue_service import DialogueStateService
from atuguigu.infrastructure.db_client import session_factory  # 有坑  模块下的成员
from atuguigu.infrastructure import  db_client                   # 包下面的模块 可以的
from atuguigu.engines.engine_builder import build_dialogue_engine


def get_dialogue_engine():
    return build_dialogue_engine()

"""
调用 get_session() 返回一个异步生成器对象，并不会立即执行函数体。
2. 当依赖注入框架（如 FastAPI 的 Depends）迭代该生成器时（通过 anext），函数体运行到 yield session 处，暂停并将 session 返回给调用方。
3. 此时 async with 的上下文尚未退出，session 处于活跃状态，可以在请求处理期间正常使用。
4. 当请求处理结束，框架会继续迭代生成器（或调用 aclose），函数体从 yield 之后恢复执行，退出 async with 块，从而自动调用 session.__aexit__() 执行清理（关闭会话、释放连接）。
这种模式确保了：
• 会话的生命周期与请求绑定（请求内共享同一个会话，请求结束后自动释放）。
• 异常安全：即使请求中抛出异常，__aexit__ 也会被触发，正确回滚事务或关闭连接。
"""
async def get_session():
    async with db_client.session_factory() as session:
        # 只能yield出去，return返回的是None,with会自动关闭session
        yield session

DialogueSessionDep = Annotated[AsyncSession,Depends(get_session)]

def get_dialogue_repository(session:DialogueSessionDep):
    return DialogueRepository(session)

DialogueEngineDep = Annotated[DialogueEngine,Depends(get_dialogue_engine)]

DialogueRepositoryDep = Annotated[DialogueRepository,Depends(get_dialogue_repository)]

def get_dialogue_service(engine:DialogueEngineDep,repository: DialogueRepositoryDep):
    return DialogueStateService(engine,repository)

DialogueStateServiceDep = Annotated[DialogueStateService,Depends(get_dialogue_service)]