from fastapi import APIRouter,WebSocket,WebSocketDisconnect
from DynamicDB.websockets.manager import manager
router=APIRouter(
    prefix="/ws",
    tags=["websocket"]
)
@router.websocket("/user/{user_id}")
async def user_websocket(
    websocket:WebSocket,
    user_id:int
):
    await manager.connect("user",user_id,websocket)
    try:
        while True:
            await websocket.receive_text()
            print("websocket loaded")
    except WebSocketDisconnect:
        manager.disconnect("user",user_id,websocket)