import sqlite3


class Database:
    def __init__(self, path="server.db"):
        self.conn = sqlite3.connect(path)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                password_hash TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                channel_id TEXT,
                author_id TEXT,
                timestamp INTEGER,
                content TEXT
            )
        """)
        self.conn.commit()

    def save_user(self, user):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO users VALUES (?, ?, ?)",
            (user.id, user.username, user.password_hash),
        )
        self.conn.commit()

    def save_message(self, channel_id, message):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO messages VALUES (?, ?, ?, ?, ?)",
            (message.id, channel_id, message.author_id, message.timestamp, message.content),
        )
        self.conn.commit()
