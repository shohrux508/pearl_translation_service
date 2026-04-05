from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.container import Container

router = APIRouter()


@router.get("/ping")
async def ping(container: Container = Depends(get_container)):
    return {"message": "pong", "status": "ok"}
