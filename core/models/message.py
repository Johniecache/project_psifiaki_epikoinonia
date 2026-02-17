import uuid
import time


class Message:
    def __init__(self, author_id: str, content: str):
        self.id = str(uuid.uuid4())
        self.author_id = author_id
        self.timestamp = int(time.time())
        self.content = content
        self.edited = False

    def edit(self, new_content: str):
        self.content = new_content
        self.edited = True
