"""WebSocket connection manager for floor-level real-time events."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class SocketManager:
    def __init__(self) -> None:
        self._rooms: dict[str, set[WebSocket]] = {}

    async def connect(self, floor_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._rooms.setdefault(floor_id, set()).add(websocket)
        logger.debug("WS connected floor=%s (clients=%d)", floor_id, len(self._rooms[floor_id]))

    def disconnect(self, floor_id: str, websocket: WebSocket) -> None:
        room = self._rooms.get(floor_id)
        if not room:
            return
        room.discard(websocket)
        if not room:
            del self._rooms[floor_id]

    async def broadcast(self, floor_id: str, event: str, data: Any) -> None:
        room = self._rooms.get(floor_id)
        if not room:
            return
        message = json.dumps({"event": event, "data": data})
        dead: list[WebSocket] = []
        for ws in room:
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(floor_id, ws)

    async def emit(self, event: str, data: Any, *, room: str) -> None:
        await self.broadcast(room, event, data)

    def emit_sync(self, event: str, data: Any, *, room: str) -> None:
        """Broadcast from sync service code (FastAPI sync route handlers)."""
        coro = self.broadcast(room, event, data)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(coro)
        except RuntimeError:
            asyncio.run(coro)


socket_manager = SocketManager()
sio = socket_manager
