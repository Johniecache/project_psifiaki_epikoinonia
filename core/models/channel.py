import uuid
from core.enums import ChannelType
from core.models.message import Message

class Channel:
    def __init__(self, name: str, channel_type: ChannelType):
        self.id = str(uuid.uuid4())
        self.name = name
        self.type = channel_type
        self.permission_overrides = {}
        self.messages: list[Message] = []
        self.active_users: set[str] = set()
        self.voice_streams: dict[str, tuple[str, int]] = {}  # user_id -> (ip, port)

    def add_message(self, message: Message):
        if self.type == ChannelType.TEXT or self.type == ChannelType.VOICE:
            self.messages.append(message)

    def join_voice(self, user_id: str, addr: tuple[str, int]):
        """Add user to voice chat; addr = (ip, port) for UDP streaming"""
        self.active_users.add(user_id)
        self.voice_streams[user_id] = addr

    def leave_voice(self, user_id: str):
        self.active_users.discard(user_id)
        if user_id in self.voice_streams:
            del self.voice_streams[user_id]
