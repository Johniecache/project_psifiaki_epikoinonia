import asyncio
import json
from auth.auth_manager import AuthManager
from core.models.server import Server
from core.models.channel import Channel
from core.models.message import Message
from core.enums import ChannelType, Permission
from persistence.database import Database


class EventServer:
    def __init__(self, host="0.0.0.0", port=8765, auth=None, community=None):
        self.host = host
        self.port = port
        self.clients = {}
        self.auth = auth
        self.community = community
        self.active_channels = {}
        self.db = Database()

        self._load_persisted_data()

    # ---------------- LOAD ON BOOT ----------------

    def _load_persisted_data(self):
        from core.enums import ChannelType

        rows = self.db.load_channels(self.community.id)

        for ch_id, name, type_str in rows:
            channel = Channel(name, ChannelType[type_str])
            channel.id = ch_id
            self.community.add_channel(channel)

            messages = self.db.load_messages(ch_id)
            for msg_id, author_id, timestamp, content in messages:
                msg = Message(author_id, content)
                msg.id = msg_id
                msg.timestamp = timestamp
                channel.messages.append(msg)

    # ---------------- NETWORK ----------------

    async def handler(self, reader, writer):
        try:
            while True:
                data = await reader.readline()
                if not data:
                    break

                message = json.loads(data.decode())
                await self.process_event(message, writer)

        except (ConnectionResetError, OSError):
            pass

        finally:
            if writer in self.clients:
                del self.clients[writer]

            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass


    async def process_event(self, message, writer):
        event = message.get("event")
        payload = message.get("payload", {})

        if event == "AUTH":
            await self.handle_auth(payload, writer)
        elif event == "MESSAGE_CREATE":
            await self.handle_message_create(payload, writer)
        elif event == "SWITCH_CHANNEL":
            await self.handle_switch_channel(payload, writer)
        elif event == "CHANNEL_CREATE":
            await self.handle_channel_create(payload, writer)
        elif event == "CHANNEL_DELETE":
            await self.handle_channel_delete(payload, writer)
        elif event == "CHANNEL_UPDATE":
            await self.handle_channel_update(payload, writer)
        elif event == "VOICE_JOIN":
            await self.handle_voice_join(payload, writer)

        elif event == "VOICE_LEAVE":
            await self.handle_voice_leave(payload, writer)

    # ---------------- AUTH ----------------

    async def handle_auth(self, payload, writer):
        username = payload.get("username")
        password = payload.get("password")

        for user in self.community.members.values():
            if user.username == username and self.auth.verify_password(password, user.password_hash):
                token = self.auth.create_session(user)
                self.clients[writer] = user.id

                await self.send_event(writer, "AUTH_SUCCESS", {
                    "token": token,
                    "user_id": user.id,
                    "channels": [
                        {
                            "id": ch.id,
                            "name": ch.name,
                            "type": ch.type.name,
                            "messages": [
                                {
                                    "id": msg.id,
                                    "author_id": msg.author_id,
                                    "content": msg.content,
                                    "timestamp": msg.timestamp
                                }
                                for msg in ch.messages
                            ]
                        }
                        for ch in self.community.channels.values()
                    ]
                })
                return

        await self.send_event(writer, "AUTH_FAILED", {"reason": "Invalid credentials"})

    # ---------------- CHANNEL CREATE ----------------

    async def handle_channel_create(self, payload, writer):
        name = payload.get("name")
        type_str = payload.get("type")

        channel = Channel(name, ChannelType[type_str])
        self.community.add_channel(channel)
        self.db.save_channel(self.community.id, channel)

        await self.broadcast({
            "event": "CHANNEL_CREATE",
            "payload": {"id": channel.id, "name": name, "type": type_str}
        })

    async def handle_channel_delete(self, payload, writer):
        channel_id = payload.get("channel_id")

        if channel_id in self.community.channels:
            del self.community.channels[channel_id]
            self.db.delete_channel(channel_id)

            await self.broadcast({
                "event": "CHANNEL_DELETE",
                "payload": {"channel_id": channel_id}
            })

    async def handle_channel_update(self, payload, writer):
        channel_id = payload.get("channel_id")
        new_name = payload.get("name")

        channel = self.community.get_channel(channel_id)
        if not channel:
            return

        channel.name = new_name
        self.db.save_channel(self.community.id, channel)

        await self.broadcast({
            "event": "CHANNEL_UPDATE",
            "payload": {"channel_id": channel_id, "name": new_name}
        })

    # ---------------- VOICE ------------------

    async def handle_voice_join(self, payload, writer):
        user_id = self.clients.get(writer)
        channel_id = payload.get("channel_id")
        udp_port = payload.get("udp_port")

        channel = self.community.get_channel(channel_id)
        if not channel:
            return

        peername = writer.get_extra_info("peername")
        ip = peername[0]

        channel.join_voice(user_id, (ip, udp_port))


    async def handle_voice_leave(self, payload, writer):
        user_id = self.clients.get(writer)
        channel_id = payload.get("channel_id")

        channel = self.community.get_channel(channel_id)
        if channel:
            channel.leave_voice(user_id)


    # ---------------- MESSAGES ----------------

    async def handle_message_create(self, payload, writer):
        user_id = self.clients.get(writer)
        channel_id = payload.get("channel_id")
        content = payload.get("content")

        channel = self.community.get_channel(channel_id)
        if not channel:
            return

        msg = Message(user_id, content)
        channel.add_message(msg)
        self.db.save_message(channel.id, msg)

        await self.broadcast({
            "event": "MESSAGE_CREATE",
            "payload": {
                "channel_id": channel.id,
                "message": {
                    "id": msg.id,
                    "author_id": msg.author_id,
                    "content": msg.content,
                    "timestamp": msg.timestamp
                }
            }
        })

    async def handle_switch_channel(self, payload, writer):
        user_id = self.clients.get(writer)
        channel_id = payload.get("channel_id")
        self.active_channels[user_id] = channel_id

        await self.send_event(writer, "CHANNEL_SWITCHED", {"channel_id": channel_id})

    # ---------------- UTIL ----------------

    async def send_event(self, writer, event, payload):
        writer.write((json.dumps({"event": event, "payload": payload}) + "\n").encode())
        await writer.drain()

    async def broadcast(self, message):
        msg = json.dumps(message) + "\n"
        for writer in self.clients:
            writer.write(msg.encode())
            await writer.drain()

    async def start(self):
        server = await asyncio.start_server(self.handler, self.host, self.port)
        async with server:
            await server.serve_forever()
