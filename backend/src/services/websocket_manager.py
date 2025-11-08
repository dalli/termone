"""WebSocket connection manager."""

from typing import Set, Dict
from fastapi import WebSocket


class WebSocketManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, client_id: str, websocket: WebSocket):
        """Accept and store WebSocket connection."""
        await websocket.accept()
        if client_id not in self.active_connections:
            self.active_connections[client_id] = set()
        self.active_connections[client_id].add(websocket)

    def disconnect(self, client_id: str, websocket: WebSocket):
        """Remove disconnected WebSocket."""
        self.active_connections[client_id].discard(websocket)

    async def broadcast(self, client_id: str, message: dict):
        """Broadcast message to all connections for a client."""
        if client_id in self.active_connections:
            for connection in self.active_connections[client_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass


def get_websocket_manager() -> WebSocketManager:
    """Get WebSocket manager instance."""
    return WebSocketManager()
