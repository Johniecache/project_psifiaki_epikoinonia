# run_event_server.py
import asyncio
from auth.auth_manager import AuthManager
from networking.event_server import EventServer
from networking.voice_server import VoiceServer
from core.models.server import Server
from core.models.role import Role
from core.models.channel import Channel
from core.enums import ChannelType, RoleType, Permission
from persistence.database import Database

db = Database()

def setup_demo():
    auth = AuthManager()
    community = Server("Demo Community")

    # Create roles
    owner_role = Role("Owner", RoleType.OWNER)
    owner_role.grant(Permission.SEND_MESSAGE)
    owner_role.grant(Permission.SPEAK)
    community.add_role(owner_role)

    # Create users
    alice = auth.create_user("alice", "password123")
    alice.assign_role(owner_role.id)
    community.add_member(alice)

    caleb = auth.create_user("caleb", "12345")
    caleb.assign_role(owner_role.id)
    community.add_member(caleb)

    # Create channels
    general = Channel("general", ChannelType.TEXT)
    voice = Channel("voice", ChannelType.VOICE)
    community.add_channel(general)
    community.add_channel(voice)

    db.save_channel(community.id, general)
    db.save_channel(community.id, voice)

    return auth, community, general, voice

async def main():
    auth, community, text_channel, voice_channel = setup_demo()

    event_server = EventServer(auth=auth, community=community)
    voice_server = VoiceServer(channel=voice_channel)

    await asyncio.gather(
        event_server.start(),
        voice_server.start()
    )

if __name__ == "__main__":
    asyncio.run(main())