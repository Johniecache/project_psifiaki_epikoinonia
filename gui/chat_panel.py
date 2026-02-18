import tkinter as tk
from tkinter import scrolledtext

class ChatPanel(tk.Frame):
    def __init__(self, parent, client_controller):
        super().__init__(parent)
        self.client_controller = client_controller

        self.chat_display = scrolledtext.ScrolledText(self, state="disabled", width=50, height=20)
        self.chat_display.pack(padx=5, pady=5)

        self.entry = tk.Entry(self)
        self.entry.pack(fill="x", padx=5, pady=5)
        self.entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self, text="Send", command=self.send_message)
        self.send_button.pack(pady=5)

        self.voice_button = tk.Button(self, text="Join Voice", command=self.toggle_voice)
        self.voice_button.pack(pady=5)

        self.disconnect_button = tk.Button(self, text="Disconnect Voice", command=self.disconnect_voice)
        self.disconnect_button.pack(pady=5)

        self.quit_button = tk.Button(self, text="Quit", command=self.quit_app)
        self.quit_button.pack(pady=5)

        self.voice_active = False

    def display_message(self, author, content):
        self.chat_display.configure(state="normal")
        self.chat_display.insert(tk.END, f"{author}: {content}\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see(tk.END)

    def send_message(self, event=None):
        content = self.entry.get()
        if not content.strip():
            return
        self.entry.delete(0, tk.END)
        self.display_message("You", content)
        self.client_controller.send_message_async(content)

    def toggle_voice(self):
        if not self.voice_active:
            self.client_controller.start_voice()
            self.voice_active = True
            self.voice_button.config(text="Voice Connected")
        else:
            self.disconnect_voice()

    def disconnect_voice(self):
        if self.voice_active:
            self.client_controller.stop_voice()
            self.voice_active = False
            self.voice_button.config(text="Join Voice")

    def quit_app(self):
        self.client_controller.shutdown()
        self.master.destroy()
