import bcrypt
import secrets
from core.models.user import User


class AuthManager:
    def __init__(self):
        self.sessions = {}

    def hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    def verify_password(self, password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode(), password_hash.encode())

    def create_user(self, username: str, password: str) -> User:
        password_hash = self.hash_password(password)
        return User(username, password_hash)

    def create_session(self, user: User) -> str:
        token = secrets.token_hex(32)
        self.sessions[token] = user.id
        user.session_token = token
        return token

    def validate_session(self, token: str) -> str | None:
        return self.sessions.get(token)
