import uvicorn
from fastapi import FastAPI
from app.config import settings
from app.container import Container
from app.api.routers import example

def create_app(container: Container) -> FastAPI:
    app = FastAPI()
    app.state.container = container
    app.include_router(example.router)
    return app

async def start_api(container: Container):
    app = create_app(container)
    config = uvicorn.Config(
        app, 
        host=settings.API_HOST, 
        port=settings.PORT, 
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()
