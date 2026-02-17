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

    def add_message(self, message: Message):
        if self.type == ChannelType.TEXT:
            self.messages.append(message)

    def join_voice(self, user_id: str):
        if self.type == ChannelType.VOICE:
            self.active_users.add(user_id)

    def leave_voice(self, user_id: str):
        self.active_users.discard(user_id)
