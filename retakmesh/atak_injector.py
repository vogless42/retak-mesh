import socket
import threading
import queue


class ATAKInjector:
    def __init__(self, config, receive_queue):
        self.config = config
        self.receive_queue = receive_queue
        self.running = False
        self.sock = None

    def start(self):
        self.running = True
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 2)
        threading.Thread(target=self._inject_loop, daemon=True).start()

    def _inject_loop(self):
        while self.running:
            try:
                data = self.receive_queue.get(timeout=1)
                self.sock.sendto(
                    data, (self.config.atak_host, self.config.atak_port)
                )
            except queue.Empty:
                continue
            except OSError:
                break

    def stop(self):
        self.running = False
        if self.sock:
            self.sock.close()
