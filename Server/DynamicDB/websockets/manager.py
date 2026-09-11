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
        print("SOCKET STORED")
        print("CONNECTIONS AFTER CONNECT:", self.connections)

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
        print("SEND CALLED")
        print("ROLE:", role)
        print("USER ID:", client_id)
        print("ACTIVE CONNECTIONS:", self.connections)
        role_connections = self.connections.get(role)

        if not role_connections:
            print("NO CONNECTIONS FOUND FOR ROLE:", role)
            return

        connections = role_connections.get(
            client_id,
            set()
        )
        if not connections:
            print(f"NO ACTIVE WEBSOCKET FOR {role} {client_id}")
            return
        disconnected = []

        for websocket in connections.copy():
            try:
                print("SENDING DATA:", data)
                await websocket.send_json(data)
                print("MESSAGE SENT SUCCESSFULLY")

            except Exception as e:
                print("WEBSOCKET SEND ERROR:", e)
                disconnected.append(websocket)

        for websocket in disconnected:
            connections.discard(websocket)

        if not connections:
            role_connections.pop(
                client_id,
                None
            )


manager = ConnectionManager()