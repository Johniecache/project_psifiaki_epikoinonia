import asyncio
from networking.server import RealtimeServer
from persistence.database import Database
from auth.auth_manager import AuthManager
from core.models.server import Server


def bootstrap():
    db = Database("server.db")
    auth = AuthManager()
    community = Server("My Community")

    return {
        "database": db,
        "auth": auth,
        "server_model": community,
    }


async def main():
    context = bootstrap()

    network_server = RealtimeServer(host="0.0.0.0", port=8765)
    print("Server running on port 8765...")
    await network_server.start()


if __name__ == "__main__":
    asyncio.run(main())
