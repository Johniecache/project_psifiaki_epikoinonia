import asyncio
from core.models.server import Server
from core.models.role import Role
from core.models.channel import Channel
from core.enums import ChannelType, RoleType, Permission
from auth.auth_manager import AuthManager
from networking.event_server import EventServer
from networking.voice_server import VoiceServer
from persistence.database import Database

db = Database()

def setup_demo():
    auth = AuthManager()
    community = Server("Demo Community")

    # Create roles
    owner_role = Role("Owner", RoleType.OWNER)
    owner_role.grant(Permission.SEND_MESSAGE)
    owner_role.grant(Permission.SPEAK)  # <-- make sure SPEAK permission exists
    community.add_role(owner_role)

    # Create demo users
    user = auth.create_user("alice", "password123")
    user.assign_role(owner_role.id)
    community.add_member(user)

    # Create a text channel (we will also allow voice)
    existing_channels = db.load_channels(community.id)

    if not existing_channels:
        text_channel = Channel("general", ChannelType.TEXT)
        community.add_channel(text_channel)
        db.save_channel(community.id, text_channel)
    else:
        text_channel = None


    # DEMO USER
    user = auth.create_user("caleb", "12345")
    user.assign_role(owner_role.id)
    community.add_member(user)

    print("Available channels:")
    for ch_id, ch in community.channels.items():
        print(f"{ch.name} -> {ch_id}")

    return auth, community, text_channel  # <-- return the channel

async def main():
    auth, community, demo_channel = setup_demo()

    # Start EventServer
    event_server = EventServer(host="0.0.0.0", port=8765, auth=auth, community=community)
    
    # Start VoiceServer for that channel
    voice_server = VoiceServer(host="0.0.0.0", port=5000, channel=demo_channel)

    # Run both servers concurrently
    await asyncio.gather(
        event_server.start(),
        voice_server.start()
    )

if __name__ == "__main__":
    asyncio.run(main())
