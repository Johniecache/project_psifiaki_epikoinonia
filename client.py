import asyncio
import json
import socket
import pyaudio
import threading

CHUNK = 960
RATE = 48000
CHANNELS = 1
FORMAT = pyaudio.paInt16
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 8765

class ClientController:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.user_id = None
        self.token = None
        self.channel_id = None
        self.connected = False
        self.message_callback = None
        self.channel_callback = None

        self.loop = asyncio.new_event_loop()
        self.client_task = None
        self.voice_task = None
        self.voice_sock = None
        self.audio = None
        self.stream_in = None
        self.stream_out = None
        self.voice_running = False

        self.muted = False
        self.deafened = False


    def set_channel_callback(self, callback):
        self.channel_callback = callback

    def set_message_callback(self, callback):
        self.message_callback = callback

    def connect_sync(self):
        def start_loop():
            asyncio.set_event_loop(self.loop)
            self.loop.run_until_complete(self._connect())
            self.loop.run_forever()

        threading.Thread(target=start_loop, daemon=True).start()

    def send_message_async(self, content):
        if self.connected and self.channel_id:
            asyncio.create_task(self._send_message(self.channel_id, content))

    def set_active_channel(self, channel_id: str):
        self.channel_id = channel_id
        asyncio.create_task(self._send({
            "event": "SWITCH_CHANNEL",
            "payload": {"channel_id": channel_id}
        }))


    async def _connect(self):
        self.reader, self.writer = await asyncio.open_connection(SERVER_HOST, SERVER_PORT)
        self.client_task = asyncio.create_task(self._listen_forever())

        # Send auth AFTER listener starts
        await self._send({
            "event": "AUTH",
            "payload": {
                "username": self.username,
                "password": self.password
            }
        })

        self.connected = True

    async def _send_message(self, channel_id, content):
        msg = {"event": "MESSAGE_CREATE", "payload": {"channel_id": channel_id, "content": content}}
        await self._send(msg)

    async def _send(self, message):
        self.writer.write((json.dumps(message) + "\n").encode())
        await self.writer.drain()

    async def _receive(self):
        line = await self.reader.readline()
        if not line:
            return {}
        return json.loads(line.decode())

    async def _listen_forever(self):
        while True:
            msg = await self._receive()
            if not msg:
                continue

            event = msg.get("event")
            payload = msg.get("payload", {})

            # ---------------- AUTH SUCCESS ----------------
            if event == "AUTH_SUCCESS":
                self.token = payload["token"]
                self.user_id = payload["user_id"]

                # Send initial channel list to GUI
                if self.channel_callback:
                    self.channel_callback({
                        "type": "INIT_CHANNELS",
                        "channels": payload.get("channels", [])
                    })

            # ---------------- CHANNEL CREATE ----------------
            elif event == "CHANNEL_CREATE":
                if self.channel_callback:
                    self.channel_callback({
                        "type": "CHANNEL_CREATE",
                        "channel": payload
                    })

            # ---------------- CHANNEL DELETE ----------------
            elif event == "CHANNEL_DELETE":
                if self.channel_callback:
                    self.channel_callback({
                        "type": "CHANNEL_DELETE",
                        "channel_id": payload["channel_id"]
                    })

            # ---------------- CHANNEL UPDATE ----------------
            elif event == "CHANNEL_UPDATE":
                if self.channel_callback:
                    self.channel_callback({
                        "type": "CHANNEL_UPDATE",
                        "channel_id": payload["channel_id"],
                        "name": payload["name"]
                    })

            # ---------------- MESSAGE ----------------
            elif event == "MESSAGE_CREATE":
                m = payload["message"]
                channel_id = payload["channel_id"]

                if self.channel_callback:
                    self.channel_callback({
                        "type": "MESSAGE_APPEND",
                        "channel_id": channel_id,
                        "message": m
                    })

                if channel_id == self.channel_id and self.message_callback:
                    self.message_callback(
                        m.get("author_id", "unknown"),
                        m.get("content", "")
                    )


            elif event == "CHANNEL_SWITCHED":
                self.channel_id = payload["channel_id"]

                        
    # ------------------ Voice ------------------
    def start_voice(self, udp_port=6000):
        if self.voice_running:
            return
        self.voice_running = True
        self.voice_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.voice_sock.bind(("", udp_port))
        # Notify server we joined voice
        asyncio.run_coroutine_threadsafe(
            self._send({
                "event": "VOICE_JOIN",
                "payload": {
                    "channel_id": self.channel_id,
                    "udp_port": udp_port
                }
            }),
            self.loop
        )
        self.audio = pyaudio.PyAudio()
        self.stream_in = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        self.stream_out = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        self.voice_task = threading.Thread(target=self._voice_loop, daemon=True)
        self.voice_task.start()

    def _voice_loop(self):
        while self.voice_running:
            try:
                if not self.muted:
                    data = self.stream_in.read(CHUNK, exception_on_overflow=False)
                    self.voice_sock.sendto(data, (SERVER_HOST, 5000))

                if not self.deafened:
                    self.voice_sock.settimeout(0.01)
                    try:
                        data, _ = self.voice_sock.recvfrom(4096)
                        self.stream_out.write(data)
                    except socket.timeout:
                        continue

            except Exception as e:
                print(f"[Voice Error] {e}")

    def toggle_mute(self):
        self.muted = not self.muted

    def toggle_deafen(self):
        self.deafened = not self.deafened

    def stop_voice(self):
        self.voice_running = False
        if self.channel_id:
            asyncio.run_coroutine_threadsafe(
                self._send({
                    "event": "VOICE_LEAVE",
                    "payload": {"channel_id": self.channel_id}
                }),
                self.loop
            )
        if self.stream_in:
            self.stream_in.stop_stream()
            self.stream_in.close()
        if self.stream_out:
            self.stream_out.stop_stream()
            self.stream_out.close()
        if self.audio:
            self.audio.terminate()
        if self.voice_sock:
            self.voice_sock.close()

    # ------------------ Shutdown ------------------
    def shutdown(self):
        self.stop_voice()
        if self.connected:
            self.writer.close()
            self.connected = False

