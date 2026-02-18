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

        self.loop = asyncio.new_event_loop()
        self.client_task = None
        self.voice_task = None
        self.voice_sock = None
        self.audio = None
        self.stream_in = None
        self.stream_out = None
        self.voice_running = False

    def set_message_callback(self, callback):
        self.message_callback = callback

    def connect_sync(self):
        asyncio.run(self._connect())

    def send_message_async(self, content):
        if self.connected and self.channel_id:
            asyncio.create_task(self._send_message(self.channel_id, content))

    async def _connect(self):
        self.reader, self.writer = await asyncio.open_connection(SERVER_HOST, SERVER_PORT)
        await self._authenticate()
        self.connected = True
        self.client_task = asyncio.create_task(self._listen_forever())

    async def _authenticate(self):
        auth_msg = {"event": "AUTH", "payload": {"username": self.username, "password": self.password}}
        await self._send(auth_msg)
        resp = await self._receive()
        if resp.get("event") == "AUTH_SUCCESS":
            self.token = resp["payload"]["token"]
            self.user_id = resp["payload"]["user_id"]
        else:
            raise Exception("Authentication failed")

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
            if msg and self.message_callback:
                payload = msg.get("payload", {})
                if "message" in payload:
                    m = payload["message"]
                    author = m.get("author_id", "unknown")
                    content = m.get("content", "")
                    self.message_callback(author, content)

    # ------------------ Voice ------------------
    def start_voice(self, udp_port=6000):
        if self.voice_running:
            return
        self.voice_running = True
        self.voice_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.voice_sock.bind(("", udp_port))
        self.audio = pyaudio.PyAudio()
        self.stream_in = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        self.stream_out = self.audio.open(format=FORMAT, channels=CHANNELS, rate=RATE, output=True, frames_per_buffer=CHUNK)
        self.voice_task = threading.Thread(target=self._voice_loop, daemon=True)
        self.voice_task.start()

    def _voice_loop(self):
        while self.voice_running:
            try:
                data = self.stream_in.read(CHUNK, exception_on_overflow=False)
                self.voice_sock.sendto(data, (SERVER_HOST, 5000))
                self.voice_sock.settimeout(0.01)
                try:
                    data, _ = self.voice_sock.recvfrom(4096)
                    self.stream_out.write(data)
                except socket.timeout:
                    continue
            except Exception as e:
                print(f"[Voice Error] {e}")

    def stop_voice(self):
        self.voice_running = False
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
