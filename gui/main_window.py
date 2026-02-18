import tkinter as tk
from gui.login_dialog import LoginDialog
from gui.chat_panel import ChatPanel

class MainWindow(tk.Tk):
    def __init__(self, client_controller):
        super().__init__()
        self.title("Python Chat Client")
        self.geometry("600x500")
        self.client_controller = client_controller

        # Login dialog
        login = LoginDialog(self, client_controller)
        if not client_controller.connected:
            self.destroy()
            return

        # Chat panel
        self.chat_panel = ChatPanel(self, client_controller)
        self.chat_panel.pack(fill="both", expand=True)

        # Bind callback for incoming messages
        client_controller.set_message_callback(self.chat_panel.display_message)
