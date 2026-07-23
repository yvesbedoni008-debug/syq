"""
WebSocket endpoint for real-time opportunity updates.
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import manager
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
import json

router = APIRouter()


@router.websocket("/ws/opportunities")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    WebSocket endpoint for real-time opportunity updates.
    Clients can connect to receive live updates when opportunities are created,
    updated, deleted, or when their scores/insights change.
    """
    # For testing purposes, we accept all connections
    # In production, you would validate the token here:
    # if not token or not validate_jwt_token(token):
    #     await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
    #     return

    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; we expect client to send ping or just wait
            data = await websocket.receive_text()
            # Echo ping/pong or handle client messages if needed
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_json({"type": "pong"})
            except Exception:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)