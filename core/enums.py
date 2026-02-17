from enum import Enum, auto


class ChannelType(Enum):
    TEXT = auto()
    VOICE = auto()


class PresenceStatus(Enum):
    ONLINE = auto()
    IDLE = auto()
    DND = auto()
    OFFLINE = auto()


class RoleType(Enum):
    OWNER = auto()
    ADMIN = auto()
    MODERATOR = auto()
    MEMBER = auto()


class Permission(Enum):
    VIEW_CHANNEL = auto()
    SEND_MESSAGE = auto()
    MANAGE_MESSAGES = auto()
    SPEAK = auto()
    MUTE_MEMBERS = auto()
    MANAGE_ROLES = auto()
    MANAGE_SERVER = auto()
