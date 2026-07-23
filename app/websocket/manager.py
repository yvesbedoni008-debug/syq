"""
WebSocket connection manager for real-time updates.
"""
from typing import Set
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # Set of active WebSocket connections
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Send a JSON message to all connected clients."""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                    # Remove broken connections
                    self.disconnect(connection)


# Global manager instance
manager = ConnectionManager()