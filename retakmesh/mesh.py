import os
import time
import threading
import RNS
from .config import RNS_CONFIG_DIR

APP_NAME = "retak"
APP_ASPECT = "cot"
ANNOUNCE_INTERVAL = 300
PEER_TIMEOUT = 900

RNODE_INTERFACE_TEMPLATE = """
  [[RNodeInterface]]
    type = RNodeInterface
    enabled = yes
    port = {port}
    frequency = {freq}
"""

RETICULUM_CONFIG_HEAD = """
[reticulum]
enable_transport = Yes
share_instance = Yes
shared_instance_port = 37428

[logging]
loglevel = 3

[interfaces]
"""


class MeshInterface:
    def __init__(self, config, receive_callback):
        self.config = config
        self.receive_callback = receive_callback
        self.peers = {}
        self.running = False

        self._ensure_reticulum_config()

        RNS.Reticulum(configdir=RNS_CONFIG_DIR, loglevel=RNS.LOG_NOTICE)

        self.destination = RNS.Destination(
            config.identity,
            RNS.Destination.IN,
            RNS.Destination.SINGLE,
            APP_NAME,
            APP_ASPECT,
        )
        self.destination.set_packet_callback(self._on_packet)
        self.destination.set_proof_strategy(RNS.Destination.PROVE_ALL)

        RNS.Transport.register_announce_handler(self._on_announce)

    def _build_reticulum_config(self):
        body = RETICULUM_CONFIG_HEAD
        if self.config.rnode_port:
            body += RNODE_INTERFACE_TEMPLATE.format(
                port=self.config.rnode_port,
                freq=self.config.rnode_freq,
            )
        return body

    def _ensure_reticulum_config(self):
        config_path = os.path.join(RNS_CONFIG_DIR, "config")
        if not os.path.exists(config_path):
            with open(config_path, "w") as f:
                f.write(self._build_reticulum_config())

    def start(self):
        self.running = True
        self._announce()
        threading.Thread(target=self._announce_loop, daemon=True).start()

    def stop(self):
        self.running = False

    def _announce(self):
        try:
            self.destination.announce()
        except Exception:
            pass

    def _announce_loop(self):
        while self.running:
            time.sleep(ANNOUNCE_INTERVAL)
            self._announce()

    def _on_announce(self, destination_hash, announced_identity, app_data):
        if announced_identity is not None:
            self.peers[destination_hash] = time.time()

    def _on_packet(self, data, packet):
        if self.receive_callback:
            self.receive_callback(bytes(data))

    def send_to_all(self, data):
        now = time.time()
        for dest_hash in list(self.peers.keys()):
            if now - self.peers[dest_hash] > PEER_TIMEOUT:
                del self.peers[dest_hash]
                continue

            identity = RNS.Identity.recall(dest_hash)
            if identity is None:
                continue

            try:
                dest = RNS.Destination(
                    identity,
                    RNS.Destination.OUT,
                    RNS.Destination.SINGLE,
                    APP_NAME,
                    APP_ASPECT,
                )
                if dest.hash != dest_hash:
                    continue

                if not RNS.Transport.has_path(dest_hash):
                    RNS.Transport.request_path(dest_hash)
                    continue

                RNS.Packet(dest, data).send()
            except Exception:
                pass
