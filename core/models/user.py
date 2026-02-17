import uuid
from core.enums import PresenceStatus


class User:
    def __init__(self, username: str, password_hash: str):
        self.id = str(uuid.uuid4())
        self.username = username
        self.password_hash = password_hash
        self.roles = set()
        self.presence = PresenceStatus.OFFLINE
        self.session_token = None

    def set_presence(self, status: PresenceStatus):
        self.presence = status

    def assign_role(self, role_id: str):
        self.roles.add(role_id)

    def remove_role(self, role_id: str):
        self.roles.discard(role_id)
