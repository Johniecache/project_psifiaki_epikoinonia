import tkinter as tk
from tkinter import simpledialog, messagebox

class LoginDialog(simpledialog.Dialog):
    def __init__(self, parent, client_controller):
        self.client_controller = client_controller
        self.username = None
        self.password = None
        super().__init__(parent, title="Login")

    def body(self, master):
        tk.Label(master, text="Username:").grid(row=0, sticky="e")
        tk.Label(master, text="Password:").grid(row=1, sticky="e")
        self.username_entry = tk.Entry(master)
        self.password_entry = tk.Entry(master, show="*")
        self.username_entry.grid(row=0, column=1)
        self.password_entry.grid(row=1, column=1)
        return self.username_entry

    def apply(self):
        self.username = self.username_entry.get()
        self.password = self.password_entry.get()
        self.client_controller.username = self.username
        self.client_controller.password = self.password
        try:
            self.client_controller.connect_sync()
        except Exception as e:
            messagebox.showerror("Login Failed", str(e))
            self.cancel()
