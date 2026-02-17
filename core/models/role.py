# core/models/role.py

import uuid
from core.enums import Permission, RoleType


class Role:
    def __init__(self, name: str, role_type: RoleType):
        self.id = str(uuid.uuid4())
        self.name = name
        self.role_type = role_type
        self.permissions: set[Permission] = set()

    def grant(self, permission: Permission):
        self.permissions.add(permission)

    def revoke(self, permission: Permission):
        self.permissions.discard(permission)

    def has(self, permission: Permission) -> bool:
        return permission in self.permissions
