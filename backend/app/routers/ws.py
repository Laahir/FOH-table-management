from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.socket_manager import socket_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/{floor_id}")
async def floor_websocket(websocket: WebSocket, floor_id: str, token: str | None = None):
    # Optional JWT — allow anonymous in dev if no token
    if token and decode_token(token) is None:
        await websocket.close(code=1008)
        return

    await socket_manager.connect(floor_id, websocket)
    try:
        while True:
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text('{"event":"pong","data":{}}')
    except WebSocketDisconnect:
        socket_manager.disconnect(floor_id, websocket)
