import sqlite3
import json

class Database:
    def __init__(self, path="server.db"):
        self.conn = sqlite3.connect(path)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id TEXT PRIMARY KEY,
                server_id TEXT,
                name TEXT,
                type TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                channel_id TEXT,
                author_id TEXT,
                timestamp INTEGER,
                content TEXT,
                reactions TEXT DEFAULT '{}'
            )
        """)

        self.conn.commit()

    # ---------------- CHANNELS ----------------

    def save_channel(self, server_id, channel):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO channels VALUES (?, ?, ?, ?)",
            (channel.id, server_id, channel.name, channel.type.name),
        )
        self.conn.commit()

    def delete_channel(self, channel_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM channels WHERE id=?", (channel_id,))
        cursor.execute("DELETE FROM messages WHERE channel_id=?", (channel_id,))
        self.conn.commit()

    def load_channels(self, server_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, name, type FROM channels WHERE server_id=?",
            (server_id,),
        )
        return cursor.fetchall()

    # ---------------- MESSAGES ----------------

    def save_message(self, channel_id, message):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO messages VALUES (?, ?, ?, ?, ?, ?)
        """, (
            message.id,
            channel_id,
            message.author_id,
            message.timestamp,
            message.content,
            json.dumps(message.reactions)
        ))
        self.conn.commit()

    def load_messages(self, channel_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, author_id, timestamp, content, reactions 
            FROM messages 
            WHERE channel_id=? 
            ORDER BY timestamp ASC
        """, (channel_id,))
        rows = cursor.fetchall()
        result = []
        for row in rows:
            msg_id, author_id, timestamp, content, reactions_json = row
            from core.models.message import Message
            msg = Message(author_id, content)
            msg.id = msg_id
            msg.timestamp = timestamp
            msg.reactions = json.loads(reactions_json) if reactions_json else {}
            if not content:
                msg.deleted = True
            result.append(msg)
        return result
