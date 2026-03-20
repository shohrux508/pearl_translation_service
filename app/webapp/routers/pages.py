from fastapi import APIRouter

router = APIRouter(tags=["webapp_api"])

@router.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "WebApp API is running"}
