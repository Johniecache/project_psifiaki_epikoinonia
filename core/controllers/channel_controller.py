from core.models.channel import Channel
from core.models.message import Message
from core.enums import ChannelType
from persistence.database import Database


class ChannelController:
    def __init__(self, server, db: Database):
        self.server = server
        self.db = db

    def create_channel(self, name: str, channel_type: ChannelType) -> Channel:
        channel = Channel(name, channel_type)
        self.server.add_channel(channel)
        self.db.save_channel(self.server.id, channel)
        return channel

    def delete_channel(self, channel_id: str) -> bool:
        if channel_id in self.server.channels:
            del self.server.channels[channel_id]
            self.db.delete_channel(channel_id)
            return True
        return False

    def update_channel(self, channel_id: str, new_name: str) -> bool:
        channel = self.server.get_channel(channel_id)
        if channel:
            channel.name = new_name
            self.db.save_channel(self.server.id, channel)
            return True
        return False

    def get_channel(self, channel_id: str = None, name: str = None) -> Channel | None:
        return self.server.get_channel(channel_id, name)

    def list_channels(self) -> list[Channel]:
        return list(self.server.channels.values())
    
    def edit_message(self, channel_id: str, message_id: str, new_content: str) -> bool:
        channel = self.server.get_channel(channel_id)
        if not channel:
            return False
        for msg in channel.messages:
            if msg.id == message_id and not msg.deleted:
                msg.edit(new_content)
                self.db.save_message(channel.id, msg)
                return True
        return False

    def delete_message(self, channel_id: str, message_id: str) -> bool:
        channel = self.server.get_channel(channel_id)
        if not channel:
            return False
        for msg in channel.messages:
            if msg.id == message_id and not msg.deleted:
                msg.delete()
                self.db.save_message(channel.id, msg)
                return True
        return False

    def add_reaction(self, channel_id: str, message_id: str, user_id: str, emoji: str) -> bool:
        channel = self.server.get_channel(channel_id)
        if not channel:
            return False
        for msg in channel.messages:
            if msg.id == message_id and not msg.deleted:
                msg.add_reaction(user_id, emoji)
                self.db.save_message(channel.id, msg)
                return True
        return False

    def remove_reaction(self, channel_id: str, message_id: str, user_id: str, emoji: str) -> bool:
        channel = self.server.get_channel(channel_id)
        if not channel:
            return False
        for msg in channel.messages:
            if msg.id == message_id and not msg.deleted:
                msg.remove_reaction(user_id, emoji)
                self.db.save_message(channel.id, msg)
                return True
        return False