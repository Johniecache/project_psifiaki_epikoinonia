import asyncio
import socket
import pyaudio

CHUNK = 960  # 20ms audio at 48kHz
RATE = 48000
CHANNELS = 1
FORMAT = pyaudio.paInt16

class VoiceServer:
    def __init__(self, host="0.0.0.0", port=5000, channel=None):
        self.host = host
        self.port = port
        self.channel = channel  # instance of Channel
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((host, port))
        self.loop = asyncio.get_event_loop()
        self.audio = pyaudio.PyAudio()
        self.stream_out = self.audio.open(format=FORMAT, channels=CHANNELS,
                                          rate=RATE, output=True, frames_per_buffer=CHUNK)

    async def start(self):
        print(f"[VoiceServer] Listening on {self.host}:{self.port}")
        while True:
            data, addr = await self.loop.sock_recvfrom(self.sock, 4096)
            print(f"[DEBUG] Received {len(data)} bytes from {addr}")
            if self.channel:
                for user_id, user_addr in self.channel.voice_streams.items():
                    if user_addr != addr:  # don't echo back
                        await self.loop.sock_sendto(self.sock, data, user_addr)
            self.stream_out.write(data)
