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

    def remove_channel(self, channel_id: str):
        if channel_id in self.channels:
            del self.channels[channel_id]

    def get_channel(self, channel_id: str | None = None, name: str | None = None):
        if channel_id and channel_id in self.channels:
            return self.channels[channel_id]
        if name:
            for ch in self.channels.values():
                if ch.name == name:
                    return ch
        return None

