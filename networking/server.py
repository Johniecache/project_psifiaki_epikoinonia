import asyncio
import json


class RealtimeServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.clients = set()

    async def handler(self, reader, writer):
        self.clients.add(writer)
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break
                await self.broadcast(data)
        finally:
            self.clients.remove(writer)
            writer.close()

    async def broadcast(self, data: bytes):
        for client in self.clients:
            client.write(data)
            await client.drain()

    async def start(self):
        server = await asyncio.start_server(self.handler, self.host, self.port)
        async with server:
            await server.serve_forever()
