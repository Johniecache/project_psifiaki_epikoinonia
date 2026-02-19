import tkinter as tk
from gui.login_dialog import LoginDialog
from gui.chat_panel import ChatPanel


class MainWindow(tk.Tk):
    def __init__(self, client_controller):
        super().__init__()

        self.title("Python Chat Client")
        self.geometry("600x800")

        self.client_controller = client_controller

        # Set channel event handler BEFORE login
        self.client_controller.set_channel_callback(self.handle_channel_event)

        # Login dialog
        login = LoginDialog(self, client_controller)
        if not client_controller.connected:
            self.destroy()
            return

        # Create chat panel
        self.chat_panel = ChatPanel(self, client_controller)
        self.chat_panel.pack(fill="both", expand=True)

        # Message callback
        client_controller.set_message_callback(self.chat_panel.display_message)

    # ---------------- CHANNEL EVENTS ----------------

    def handle_channel_event(self, data):
        event_type = data.get("type")

        # ---------------- INIT ----------------
        if event_type == "INIT_CHANNELS":
            for ch in data["channels"]:
                self.chat_panel.add_channel_from_server(ch)

            self.chat_panel.refresh_channel_list()

        # ---------------- CREATE ----------------
        elif event_type == "CHANNEL_CREATE":
            self.chat_panel.add_channel_from_server(data["channel"])
            self.chat_panel.refresh_channel_list()

        # ---------------- DELETE ----------------
        elif event_type == "CHANNEL_DELETE":
            self.chat_panel.remove_channel_from_server(data["channel_id"])
            self.chat_panel.refresh_channel_list()

        # ---------------- UPDATE ----------------
        elif event_type == "CHANNEL_UPDATE":
            self.chat_panel.update_channel_from_server(
                data["channel_id"],
                data["name"]
            )
            self.chat_panel.refresh_channel_list()

        # ---------------- MESSAGE APPEND ----------------
        elif event_type == "MESSAGE_APPEND":
            channel_id = data["channel_id"]
            message = data["message"]

            channel = self.chat_panel.channels.get(channel_id)
            if channel:
                from core.models.message import Message
                msg_obj = Message(message["author_id"], message["content"])
                msg_obj.id = message["id"]
                msg_obj.timestamp = message["timestamp"]
                channel.messages.append(msg_obj)
