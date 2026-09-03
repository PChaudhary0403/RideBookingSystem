from fastapi import APIRouter,WebSocket,WebSocketDisconnect
from DynamicDB.websockets.manager import manager
router=APIRouter(
    prefix="/ws",
    tags=["websocket"]
)
@router.websocket("/driver/{driver_id}")
async def driver_websocket(
    websocket:WebSocket,
    driver_id:int
):
    await manager.connect(driver_id,websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(driver_id)