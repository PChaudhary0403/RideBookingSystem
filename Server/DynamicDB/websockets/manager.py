from fastapi import WebSocket
class ConnectionManager:
    def __init__(self):
        self.active_connections={}
    async def connect(self,driver_id:int,websocket:WebSocket):
        await websocket.accept()
        self.active_connections[driver_id]=websocket

    def disconnect(self,driver_id:int):
        self.active_connections.pop(driver_id,None)

    async def send_to_driver(self,driver_id:int,data:dict):
        websocket=self.active_connections.get(driver_id)
        if websocket:
            await websocket.send_json(data)

manager=ConnectionManager()