from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):

        self.connections = {
            "driver": {},
            "user": {}
        }


    async def connect(
        self,
        role: str,
        client_id: int,
        websocket: WebSocket
    ):
        await websocket.accept()

        role_connections = self.connections[role]

        if client_id not in role_connections:
            role_connections[client_id] = set()

        role_connections[client_id].add(websocket)


    def disconnect(
        self,
        role: str,
        client_id: int,
        websocket: WebSocket
    ):
        role_connections = self.connections.get(role)

        if not role_connections:
            return

        connections = role_connections.get(client_id)

        if not connections:
            return

        connections.discard(websocket)

        if not connections:
            role_connections.pop(client_id, None)


    async def send(
        self,
        role: str,
        client_id: int,
        data: dict
    ):
        role_connections = self.connections.get(role)

        if not role_connections:
            return

        connections = role_connections.get(
            client_id,
            set()
        )

        disconnected = []

        for websocket in connections.copy():
            try:
                await websocket.send_json(data)

            except Exception:
                disconnected.append(websocket)

        for websocket in disconnected:
            connections.discard(websocket)

        if not connections:
            role_connections.pop(
                client_id,
                None
            )


manager = ConnectionManager()