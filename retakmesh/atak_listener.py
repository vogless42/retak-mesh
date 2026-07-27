import socket
import struct
import threading


class ATAKListener:
    def __init__(self, config, callback):
        self.config = config
        self.callback = callback
        self.running = False
        self.sock = None

    def start(self):
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        group = socket.inet_aton(self.config.atak_host)
        membership = struct.pack("4s4s", group, socket.inet_aton("0.0.0.0"))
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, membership)
        self.sock.bind(("", self.config.atak_port))

        threading.Thread(target=self._listen_loop, daemon=True).start()

    def _listen_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(4096)
                if self.callback:
                    self.callback(data)
            except OSError:
                break

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
