# core/models/message.py
import uuid
import time

class Message:
    def __init__(self, author_id: str, content: str):
        self.id = str(uuid.uuid4())
        self.author_id = author_id
        self.timestamp = int(time.time())
        self.content = content
        self.edited = False
        self.deleted = False
        self.reactions: dict[str, set[str]] = {}  # emoji -> set of user_ids

    def edit(self, new_content: str):
        if not self.deleted:
            self.content = new_content
            self.edited = True

    def delete(self):
        self.deleted = True
        self.content = ""

    def add_reaction(self, user_id: str, emoji: str):
        if emoji not in self.reactions:
            self.reactions[emoji] = set()
        self.reactions[emoji].add(user_id)

    def remove_reaction(self, user_id: str, emoji: str):
        if emoji in self.reactions and user_id in self.reactions[emoji]:
            self.reactions[emoji].discard(user_id)
            if not self.reactions[emoji]:
                del self.reactions[emoji]