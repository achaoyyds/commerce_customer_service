import uvicorn

from atuguigu.config.settings import settings

if __name__ == '__main__':
    uvicorn.run(app = "atuguigu.api.app:app",host=settings.app_host,port=settings.app_port)