import uuid
from core.models.user import User
from core.models.role import Role
from core.models.channel import Channel


class Server:
    def __init__(self, name: str):
        self.id = str(uuid.uuid4())
        self.name = name
        self.members: dict[str, User] = {}
        self.roles: dict[str, Role] = {}
        self.channels: dict[str, Channel] = {}

    def add_member(self, user: User):
        self.members[user.id] = user

    def add_role(self, role: Role):
        self.roles[role.id] = role

    def add_channel(self, channel: Channel):
        self.channels[channel.id] = channel

    def get_channel(self, channel_id: str):
        return self.channels.get(channel_id)

