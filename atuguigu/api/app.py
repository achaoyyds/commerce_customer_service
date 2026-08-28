from fastapi import FastAPI
from atuguigu.api.chat_router import router
from atuguigu.admin.router import router as admin_router
from atuguigu.admin.knowledge_router import router as knowledge_router
from atuguigu.admin.flow_router import router as flow_router
from atuguigu.admin.release_router import router as release_router
from atuguigu.admin.user_router import router as user_router
from atuguigu.observability.router import router as dashboard_router
from atuguigu.infrastructure.db_client import init_db_engine,dispose_engine
from atuguigu.infrastructure.http_client import init_http_client,close_http_client


async def lifespan(_:FastAPI):
    """
    fastapi 生命周期的回调函数
    Args:
        _:

    Returns:

    """

    # 1.初始化各种资源
    print("应用启动的时候，执行回调函数")
    init_db_engine()
    init_http_client()

    # 2.真正执行路由请求
    yield

    await dispose_engine()
    await close_http_client()

app = FastAPI(description="智能客服项目",lifespan=lifespan)

app.include_router(router)
app.include_router(admin_router)
app.include_router(knowledge_router)
app.include_router(flow_router)
app.include_router(release_router)
app.include_router(user_router)
app.include_router(dashboard_router)


