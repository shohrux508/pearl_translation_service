import os
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.config import settings
from app.container import Container
from app.webapp.routers import pages

def create_webapp(container: Container) -> FastAPI:
    app = FastAPI(title="Telegram WebApp")
    app.state.container = container
    
    from app.webapp.routers import pages_router, api_router
    app.include_router(pages_router)
    app.include_router(api_router)
    
    # Mount frontend dist folder
    frontend_dir = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "dist")
    
    # Check if dir exists (might not exist on first run before vite build)
    if os.path.exists(frontend_dir):
        app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")
        
        @app.get("/{full_path:path}")
        async def catch_all(full_path: str):
            return FileResponse(os.path.join(frontend_dir, "index.html"))
    else:
        import logging
        logging.getLogger(__name__).warning("Frontend build directory not found. Run 'npm run build' in frontend folder.")

    return app

async def start_webapp(container: Container):
    app = create_webapp(container)
    config = uvicorn.Config(
        app, 
        host=settings.API_HOST, 
        port=settings.WEBAPP_PORT, 
        log_level="info"
    )
    server = uvicorn.Server(config)
    await server.serve()
