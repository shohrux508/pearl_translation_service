from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/ping")
async def ping(request: Request):
    container = request.app.state.container
    example_service = container.get("example_service")
    msg = example_service.get_message()
    return {"message": f"API says: {msg}"}
