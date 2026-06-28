from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.socket_manager import manager

router = APIRouter(tags=["ws"])


@router.get("/ws")
def websocket_info() -> dict:
    """WebSocket connections are not listed as interactive routes — use the URL below."""
    return {
        "connectUrl": "ws://localhost:8000/ws/{floor_id}?token=<jwt>",
        "events": ["table_updated", "ai_alert", "order_placed", "payment_confirmed"],
    }


@router.websocket("/ws/{floor_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    floor_id: str,
    token: str | None = Query(None),
) -> None:
    if not token or not decode_token(token):
        await websocket.close(code=1008)
        return
    await manager.connect(websocket, floor_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, floor_id)
