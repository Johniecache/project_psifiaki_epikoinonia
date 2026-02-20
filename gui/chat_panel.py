import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
from core.enums import ChannelType
import asyncio
from core.models.channel import Channel
from core.enums import ChannelType
from gui.settings.settings_window import SettingsWindow

class ChatPanel(tk.Frame):
    def __init__(self, parent, client_controller):
        super().__init__(parent)
        self.client_controller = client_controller
        self.channels: dict[str, object] = {}  # channel_id -> Channel instance
        self.channel: object | None = None

        # ---------------- UI ----------------
        # Sidebar container (list + buttons)
        self.sidebar_frame = tk.Frame(self)
        self.sidebar_frame.pack(side="left", fill="y", padx=5, pady=5)

        # Channel list
        self.channel_listbox = tk.Listbox(self.sidebar_frame)
        self.channel_listbox.pack(side="top", fill="y", expand=True)
        self.channel_listbox.bind("<<ListboxSelect>>", self.on_channel_select)

        # -------- Channel Buttons Container --------
        self.channel_buttons_frame = tk.Frame(self.sidebar_frame)
        self.channel_buttons_frame.pack(side="top", pady=5)

        # Top row: Add & Edit
        self.top_button_row = tk.Frame(self.channel_buttons_frame)
        self.top_button_row.pack(side="top", pady=2)

        self.add_button = tk.Button(self.top_button_row, text="Add", command=self.add_channel_dialog)
        self.add_button.pack(side="left", padx=2)

        self.edit_button = tk.Button(self.top_button_row, text="Edit", command=self.edit_channel_dialog)
        self.edit_button.pack(side="left", padx=2)

        # Bottom row: Remove centered
        self.bottom_button_row = tk.Frame(self.channel_buttons_frame)
        self.bottom_button_row.pack(side="top", pady=2)

        self.remove_button = tk.Button(self.bottom_button_row, text="Remove", command=self.remove_channel)
        self.remove_button.pack()

        # Chat area
        self.chat_display = scrolledtext.ScrolledText(self, state="disabled", width=50, height=20)
        self.chat_display.pack(side="top", fill="both", expand=True, padx=5, pady=5)

        self.chat_display.bind("<Button-3>", self.on_right_click)

        # ---- Message input row ----
        self.input_frame = tk.Frame(self)
        self.input_frame.pack(fill="x", padx=5, pady=5)

        self.entry = tk.Entry(self.input_frame)
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self.send_message)

        self.send_button = tk.Button(self.input_frame, text="Send", command=self.send_message)
        self.send_button.pack(side="right", padx=5)

        # ----------------- Settings -----------------
        self.settings_button = tk.Button(self, text="⚙", command=self.open_settings)
        self.settings_button.pack(side="top", anchor="ne", padx=5, pady=5)

        # ---- Voice Row 1 (Join + Mute) ----
        self.voice_row1 = tk.Frame(self)
        self.voice_row1.pack(pady=5)

        self.voice_button = tk.Button(
            self.voice_row1,
            text="Join Voice",
            command=self.toggle_voice,
            state="disabled"
        )
        self.voice_button.pack(side="left", padx=5)

        self.mute_button = tk.Button(
            self.voice_row1,
            text="Mute",
            command=self.toggle_mute
        )
        self.mute_button.pack(side="left", padx=5)

        # ---- Voice Row 2 (Disconnect + Deafen) ----
        self.voice_row2 = tk.Frame(self)
        self.voice_row2.pack(pady=5)

        self.disconnect_button = tk.Button(
            self.voice_row2,
            text="Disconnect Voice",
            command=self.disconnect_voice
        )
        self.disconnect_button.pack(side="left", padx=5)

        self.deafen_button = tk.Button(
            self.voice_row2,
            text="Deafen",
            command=self.toggle_deafen
        )
        self.deafen_button.pack(side="left", padx=5)


        # ----------------- Quit -----------------
        self.quit_button = tk.Button(self, text="Quit", command=self.quit_app)
        self.quit_button.pack(side="bottom", pady=5)

        self.voice_active = False

    # ---------------- Channel Management ----------------
    def add_channel(self, channel):
        self.channels[channel.id] = channel
        self.channel_listbox.insert(tk.END, channel.name)
        if not self.channel:
            self.set_channel(channel)
            self.channel_listbox.selection_set(0)
            # Use run_coroutine_threadsafe instead of create_task
            if self.client_controller.loop.is_running():
                asyncio.run_coroutine_threadsafe(
                    self.client_controller._send({"event": "SWITCH_CHANNEL", "payload": {"channel_id": channel.id}}),
                    self.client_controller.loop
                )
            self.client_controller.channel_id = channel.id

    def add_channel_dialog(self):
        name = simpledialog.askstring("Channel Name", "Enter channel name:")
        if not name:
            return
        type_choice = messagebox.askquestion("Channel Type", "Text channel? (No = Voice)")
        channel_type = "TEXT" if type_choice == "yes" else "VOICE"

        if self.client_controller.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.client_controller._send({
                    "event": "CHANNEL_CREATE",
                    "payload": {"name": name, "type": channel_type}
                }),
                self.client_controller.loop
            )

    def edit_channel_dialog(self):
        if not self.channel:
            messagebox.showwarning("No channel selected", "Select a channel to edit")
            return

        new_name = simpledialog.askstring(
            "Edit Channel",
            "New channel name:",
            initialvalue=self.channel.name
        )

        if not new_name or not new_name.strip():
            return

        channel_id = self.channel.id

        # Send update to server
        if self.client_controller.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.client_controller._send({
                    "event": "CHANNEL_UPDATE",
                    "payload": {
                        "channel_id": channel_id,
                        "name": new_name.strip()
                    }
                }),
                self.client_controller.loop
            )

    def open_settings(self):
        SettingsWindow(self)

    def add_channel_from_server(self, channel_data):
        channel = Channel(
            channel_data["name"],
            ChannelType[channel_data["type"]]
        )
        channel.id = channel_data["id"]

        # Load message history
        for msg_data in channel_data.get("messages", []):
            from core.models.message import Message
            msg = Message(msg_data["author_id"], msg_data["content"])
            msg.id = msg_data["id"]
            msg.timestamp = msg_data["timestamp"]
            channel.messages.append(msg)

        self.channels[channel.id] = channel

    def remove_channel_from_server(self, channel_id):
        if channel_id in self.channels:
            del self.channels[channel_id]
            self.refresh_channel_list()


    def update_channel_from_server(self, channel_id, new_name):
        channel = self.channels.get(channel_id)
        if channel:
            channel.name = new_name
            self.refresh_channel_list()

    def remove_channel(self):
        if not self.channel:
            messagebox.showwarning("No channel selected", "Select a channel to remove")
            return

        channel_id = self.channel.id

        # Send delete event to server
        if self.client_controller.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.client_controller._send({
                    "event": "CHANNEL_DELETE",
                    "payload": {"channel_id": channel_id}
                }),
                self.client_controller.loop
            )

        # Clear local selection immediately
        self.channel = None
        self.voice_button.config(state="disabled")
        self.chat_display.configure(state="normal")
        self.chat_display.delete(1.0, tk.END)
        self.chat_display.configure(state="disabled")


    def refresh_channel_list(self):
        self.channel_listbox.delete(0, tk.END)
        for ch in self.channels.values():
            self.channel_listbox.insert(tk.END, ch.name)

    def on_channel_select(self, event):
        selection = self.channel_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        channel_name = self.channel_listbox.get(index)
        for ch in self.channels.values():
            if ch.name == channel_name:
                self.set_channel(ch)
                # Switch channel on server safely
                if self.client_controller.loop.is_running():
                    asyncio.run_coroutine_threadsafe(
                        self.client_controller._send({"event": "SWITCH_CHANNEL", "payload": {"channel_id": ch.id}}),
                        self.client_controller.loop
                    )
                self.client_controller.channel_id = ch.id
                break

    def set_channel(self, channel):
        self.channel = channel
        if channel.type == ChannelType.TEXT:
            self.voice_button.config(state="disabled")
        else:
            self.voice_button.config(state="normal")

        self.chat_display.configure(state="normal")
        self.chat_display.delete(1.0, tk.END)
        for msg in channel.messages:
            self.display_message(msg.author_id, msg.content)
        self.chat_display.configure(state="disabled")

    # ---------------- Right Click ----------------
    def on_right_click(self, event):
        try:
            index = self.chat_display.index(f"@{event.x},{event.y}")
            line_num = int(index.split('.')[0])
            line_text = self.chat_display.get(f"{line_num}.0", f"{line_num}.end").strip()
            if not line_text:
                return
            menu = tk.Menu(self, tearoff=0)
            menu.add_command(label="Edit", command=lambda: self.edit_message_dialog(line_num))
            menu.add_command(label="Delete", command=lambda: self.delete_message(line_num))
            menu.add_command(label="React", command=lambda: self.react_message_dialog(line_num))
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def edit_message_dialog(self, line_num):
        msg_text = self.chat_display.get(f"{line_num}.0", f"{line_num}.end").strip()
        new_text = tk.simpledialog.askstring("Edit Message", "New content:", initialvalue=msg_text)
        if new_text and self.client_controller.channel_id:
            msg_id = self.channel.messages[line_num-1].id
            asyncio.run_coroutine_threadsafe(
                self.client_controller.edit_message(self.channel.id, msg_id, new_text),
                self.client_controller.loop
            )

    def delete_message(self, line_num):
        if self.client_controller.channel_id:
            msg_id = self.channel.messages[line_num-1].id
            asyncio.run_coroutine_threadsafe(
                self.client_controller.delete_message(self.channel.id, msg_id),
                self.client_controller.loop
            )

    def react_message_dialog(self, line_num):
        emoji = tk.simpledialog.askstring("React", "Enter emoji:")
        if emoji and self.client_controller.channel_id:
            msg_id = self.channel.messages[line_num-1].id
            asyncio.run_coroutine_threadsafe(
                self.client_controller.add_reaction(self.channel.id, msg_id, emoji),
                self.client_controller.loop
            )

    # ---------------- Messaging ----------------
    def display_message(self, author, content):
        self.chat_display.configure(state="normal")
        self.chat_display.insert(tk.END, f"{author}: {content}\n")
        self.chat_display.configure(state="disabled")
        self.chat_display.see(tk.END)

    def send_message(self, event=None):
        if not self.channel:
            messagebox.showwarning("No channel", "Select a channel first")
            return
        content = self.entry.get()
        if not content.strip():
            return
        self.entry.delete(0, tk.END)

        # Send message safely on asyncio loop
        if self.client_controller.loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self.client_controller._send_message(self.channel.id, content),
                self.client_controller.loop
            )

    # ---------------- Voice ----------------
    def toggle_voice(self):
        if not self.channel:
            messagebox.showwarning("No channel", "Select a voice channel first")
            return
        if self.channel.type != ChannelType.VOICE:
            messagebox.showwarning("Invalid channel", "Cannot join voice on a text channel")
            return

        if not self.voice_active:
            self.client_controller.start_voice()
            self.voice_active = True
            self.voice_button.config(text="Voice Connected")
        else:
            self.disconnect_voice()

    def toggle_mute(self):
        self.client_controller.toggle_mute()
        self.mute_button.config(
            text="Unmute" if self.client_controller.muted else "Mute"
        )

    def toggle_deafen(self):
        self.client_controller.toggle_deafen()
        self.deafen_button.config(
            text="Undeafen" if self.client_controller.deafened else "Deafen"
        )


    def disconnect_voice(self):
        if self.voice_active:
            self.client_controller.stop_voice()
            self.voice_active = False
            self.voice_button.config(text="Join Voice")

    # ---------------- Shutdown ----------------
    def quit_app(self):
        self.client_controller.shutdown()
        self.master.destroy()
