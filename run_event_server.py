import asyncio
from core.models.server import Server
from core.models.role import Role
from core.models.channel import Channel
from core.enums import ChannelType, RoleType, Permission
from auth.auth_manager import AuthManager
from networking.event_server import EventServer

def setup_demo():
    auth = AuthManager()
    community = Server("Demo Community")

    # Create roles
    owner_role = Role("Owner", RoleType.OWNER)
    owner_role.grant(Permission.SEND_MESSAGE)
    community.add_role(owner_role)

    # Create demo users
    user = auth.create_user("alice", "password123")
    user.assign_role(owner_role.id)
    community.add_member(user)

    # Create a text channel
    text_channel = Channel("general", ChannelType.TEXT)
    community.add_channel(text_channel)

    # DEMO USER
    user = auth.create_user("caleb", "12345")
    user.assign_role(owner_role.id)
    community.add_member(user)

    print("Available channels:")
    for ch_id, ch in community.channels.items():
        print(f"{ch.name} -> {ch_id}")


    return auth, community


async def main():
    auth, community = setup_demo()
    server = EventServer(host="0.0.0.0", port=8765, auth=auth, community=community)
    await server.start()


if __name__ == "__main__":
    asyncio.run(main())
