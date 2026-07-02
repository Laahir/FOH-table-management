import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    def __init__(self) -> None:
        self._rooms: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, floor_id: str) -> None:
        await websocket.accept()
        self._rooms.setdefault(floor_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, floor_id: str) -> None:
        room = self._rooms.get(floor_id, [])
        if websocket in room:
            room.remove(websocket)
        if not room:
            self._rooms.pop(floor_id, None)

    async def broadcast(self, floor_id: str, event: str, data: dict[str, Any]) -> None:
        message = json.dumps({"event": event, "data": data})
        dead: list[WebSocket] = []
        for ws in self._rooms.get(floor_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, floor_id)


manager = ConnectionManager()


def emit_sync(event: str, data: dict[str, Any], room: str) -> None:
    """Emit a WebSocket event from synchronous service code.

    Routes through the single shared ``manager`` instance so every caller —
    whether it uses ``sio.emit_sync`` or the module-level ``emit_sync`` —
    reaches the exact same connected clients.
    """
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(room, event, data))
    except RuntimeError:
        try:
            asyncio.run(manager.broadcast(room, event, data))
        except Exception as exc:
            logger.debug("WebSocket emit skipped: %s", exc)


class _SocketEmitter:
    """Emitter facade over the shared ``manager`` instance.

    Exposes both an async ``emit`` and a synchronous ``emit_sync`` so callers
    in either context hit the same rooms. There is only ONE ``manager`` and
    ONE ``sio`` in the process — no duplicate instances.
    """

    async def emit(self, event: str, data: dict[str, Any], room: str) -> None:
        await manager.broadcast(room, event, data)

    def emit_sync(self, event: str, data: dict[str, Any], room: str) -> None:
        emit_sync(event, data, room)


sio = _SocketEmitter()
