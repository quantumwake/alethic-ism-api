from fastapi import APIRouter
from fastapi.websockets import WebSocket


state_channel_router = APIRouter()

@state_channel_router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    while True:
        data = await websocket.receive_text()
        await websocket.send_text(f"Message text was: {data}")