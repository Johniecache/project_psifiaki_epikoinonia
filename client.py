import asyncio
import json

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8765


class EventClient:
    def __init__(self, username: str, password: str):
        self.username = username
        self.password = password
        self.reader: asyncio.StreamReader = None
        self.writer: asyncio.StreamWriter = None
        self.user_id = None
        self.token = None

    async def connect(self):
        self.reader, self.writer = await asyncio.open_connection(SERVER_HOST, SERVER_PORT)
        print(f"Connected to server at {SERVER_HOST}:{SERVER_PORT}")
        await self.authenticate()

    async def authenticate(self):
        auth_msg = {
            "event": "AUTH",
            "payload": {"username": self.username, "password": self.password}
        }
        await self.send(auth_msg)
        response = await self.receive()
        if response.get("event") == "AUTH_SUCCESS":
            self.token = response["payload"]["token"]
            self.user_id = response["payload"]["user_id"]
            print(f"Authenticated successfully as {self.username} (user_id={self.user_id})")
        else:
            print("Authentication failed:", response.get("payload"))
            exit(1)

    async def send_message(self, channel_id: str, content: str):
        msg = {
            "event": "MESSAGE_CREATE",
            "payload": {"channel_id": channel_id, "content": content}
        }
        await self.send(msg)

    async def send(self, message: dict):
        self.writer.write((json.dumps(message) + "\n").encode())
        await self.writer.drain()

    async def receive(self) -> dict:
        line = await self.reader.readline()
        if not line:
            return {}
        return json.loads(line.decode())

    async def listen_forever(self):
        while True:
            msg = await self.receive()
            if msg:
                print("EVENT:", msg)


async def main():
    username = input("Username: ")
    password = input("Password: ")

    client = EventClient(username, password)
    await client.connect()

    # Start listening in background
    asyncio.create_task(client.listen_forever())

    # Simple input loop to send messages
    channel_id = input("Enter channel ID to send messages to: ")
    while True:
        content = input("> ")
        if content.lower() in ("quit", "exit"):
            break
        await client.send_message(channel_id, content)


if __name__ == "__main__":
    asyncio.run(main())
