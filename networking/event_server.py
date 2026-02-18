import asyncio
import json
from auth.auth_manager import AuthManager
from core.models.server import Server
from core.models.channel import Channel
from core.models.message import Message
from core.enums import ChannelType, Permission 


class EventServer:
    def __init__(self, host="0.0.0.0", port=8765, auth: AuthManager = None, community: Server = None):
        self.host = host
        self.port = port
        self.clients: dict[asyncio.StreamWriter, str] = {}  # writer -> user_id
        self.auth = auth
        self.community = community

    async def handler(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        addr = writer.get_extra_info('peername')
        print(f"[DEBUG] Connection from {addr}", flush=True)

        try:
            while True:
                data = await reader.readline()
                if not data:
                    print("[DEBUG] Client disconnected", flush=True)
                    break

                print(f"[DEBUG] Raw data received: {data}", flush=True)

                try:
                    message = json.loads(data.decode())
                    print(f"[DEBUG] Parsed JSON: {message}", flush=True)
                    await self.process_event(message, writer)
                except json.JSONDecodeError:
                    print("[DEBUG] Invalid JSON received", flush=True)
                    await self.send_error(writer, "Invalid JSON format")

        except Exception as e:
            print(f"[DEBUG] Exception: {e}", flush=True)

        finally:
            if writer in self.clients:
                del self.clients[writer]
            writer.close()
            await writer.wait_closed()


    async def process_event(self, message: dict, writer: asyncio.StreamWriter):
        event = message.get("event")
        payload = message.get("payload", {})

        if event == "AUTH":
            await self.handle_auth(payload, writer)
        elif event == "MESSAGE_CREATE":
            await self.handle_message_create(payload, writer)
        elif event == "VOICE_JOIN":
            await self.handle_voice_join(payload, writer)
        else:
            await self.send_error(writer, f"Unknown event: {event}")

    async def handle_auth(self, payload: dict, writer: asyncio.StreamWriter):
        username = payload.get("username")
        password = payload.get("password")

        for user in self.community.members.values():
            if user.username == username and self.auth.verify_password(password, user.password_hash):
                token = self.auth.create_session(user)
                self.clients[writer] = user.id
                await self.send_event(writer, "AUTH_SUCCESS", {"token": token, "user_id": user.id})
                print(f"User {username} authenticated")
                return

        await self.send_event(writer, "AUTH_FAILED", {"reason": "Invalid credentials"})

    async def handle_voice_join(self, payload: dict, writer: asyncio.StreamWriter):
        user_id = self.clients.get(writer)
        if not user_id:
            await self.send_error(writer, "Not authenticated")
            return

        channel_id = payload.get("channel_id")
        udp_port = payload.get("udp_port")
        peer_ip = writer.get_extra_info("peername")[0]

        channel = self.community.channels.get(channel_id)
        if not channel:
            await self.send_error(writer, "Invalid channel")
            return

        # Add user to voice in channel
        channel.join_voice(user_id, (peer_ip, udp_port))
        await self.send_event(writer, "VOICE_JOINED", {"channel_id": channel.id})

    async def handle_message_create(self, payload: dict, writer: asyncio.StreamWriter):
        user_id = self.clients.get(writer)
        if not user_id:
            await self.send_error(writer, "Not authenticated")
            return

        channel_id = payload.get("channel_id")
        content = payload.get("content")

        channel = self.community.channels.get(channel_id)

        if not channel:
            # fallback: lookup by name
            for ch in self.community.channels.values():
                if ch.name == channel_id:
                    channel = ch
                    break

        if not channel:
            await self.send_error(writer, "Invalid channel")
            return


        # Check permissions (simplified)
        user = self.community.members[user_id]
        allowed = False
        for role_id in user.roles:
            role = self.community.roles.get(role_id)
            if role and Permission.SEND_MESSAGE in role.permissions:
                allowed = True
                break

        if not allowed:
            await self.send_error(writer, "Permission denied")
            return

        msg = Message(author_id=user_id, content=content)
        channel.add_message(msg)

        # Broadcast to all connected users
        await self.broadcast_event("MESSAGE_CREATE", {
            "channel_id": channel.id,
            "message": {
                "id": msg.id,
                "author_id": msg.author_id,
                "content": msg.content,
                "timestamp": msg.timestamp
            }
        })

    async def send_event(self, writer: asyncio.StreamWriter, event: str, payload: dict):
        writer.write((json.dumps({"event": event, "payload": payload}) + "\n").encode())
        await writer.drain()

    async def send_error(self, writer: asyncio.StreamWriter, reason: str):
        await self.send_event(writer, "ERROR", {"reason": reason})

    async def broadcast_event(self, event: str, payload: dict):
        msg = json.dumps({"event": event, "payload": payload}) + "\n"
        for writer in self.clients.keys():
            writer.write(msg.encode())
            await writer.drain()

    async def start(self):
        server = await asyncio.start_server(self.handler, self.host, self.port)
        print(f"EventServer running on {self.host}:{self.port}")
        async with server:
            await server.serve_forever()
