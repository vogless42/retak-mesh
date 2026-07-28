import os
import sys
import pty
import socket
import select
import signal
import argparse
import threading
import queue

from retakmesh.config import Config
from retakmesh.mesh import MeshInterface
from retakmesh.atak_listener import ATAKListener
from retakmesh.atak_injector import ATAKInjector


def start_tcp_rnode_bridge(host, port):
    """Connect to a TCP server and bridge it to a local PTY.
    Returns the PTY path for use as an RNode serial port."""
    master_fd, slave_fd = pty.openpty()
    slave_name = os.ttyname(slave_fd)

    running = True

    def tcp_bridge():
        nonlocal running
        while running:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((host, port))
                sock.settimeout(None)
                print(f"[retak-mesh] TCP bridge connected to {host}:{port}")
            except Exception as e:
                if running:
                    print(f"[retak-mesh] TCP bridge retrying in 5s... ({e})")
                threading.Event().wait(5)
                continue

            try:
                poll = select.poll()
                poll.register(sock, select.POLLIN)
                poll.register(master_fd, select.POLLIN)

                while running:
                    events = poll.poll(1000)
                    for fd, _ in events:
                        if fd == sock.fileno():
                            data = sock.recv(4096)
                            if not data:
                                raise ConnectionError("TCP closed")
                            os.write(master_fd, data)
                        elif fd == master_fd:
                            data = os.read(master_fd, 4096)
                            if not data:
                                raise ConnectionError("PTY closed")
                            sock.sendall(data)
            except Exception as e:
                print(f"[retak-mesh] TCP bridge disconnected: {e}")
            finally:
                try:
                    sock.close()
                except Exception:
                    pass

    t = threading.Thread(target=tcp_bridge, daemon=True)
    t.start()

    return slave_name


def main():
    parser = argparse.ArgumentParser(description="retak-mesh: ATAK over Reticulum bridge")
    parser.add_argument("--rnode-port", type=str, default=None, help="RNode serial port or tcp:host:port")
    parser.add_argument("--freq", type=int, default=None, help="RNode frequency in Hz")
    args = parser.parse_args()

    config = Config()
    if args.rnode_port:
        config.rnode_port = args.rnode_port
    if args.freq:
        config.rnode_freq = args.freq

    tx_queue = queue.Queue()
    rx_queue = queue.Queue()

    if config.rnode_port and config.rnode_port.startswith("tcp:"):
        parts = config.rnode_port[4:].split(":")
        host = parts[0]
        port = int(parts[1]) if len(parts) > 1 else 9090
        print(f"[retak-mesh] Creating TCP bridge to {host}:{port}...")
        pty_path = start_tcp_rnode_bridge(host, port)
        print(f"[retak-mesh] TCP bridge ready at PTY {pty_path}")
        config.rnode_port = pty_path

    mesh = MeshInterface(config, rx_queue.put)
    listener = ATAKListener(config, tx_queue.put)
    injector = ATAKInjector(config, rx_queue)

    def bridge():
        while True:
            try:
                data = tx_queue.get()
                if data is None:
                    break
                mesh.send_to_all(data)
            except Exception:
                continue

    bridge_thread = threading.Thread(target=bridge, daemon=True)

    mesh.start()
    listener.start()
    injector.start()
    bridge_thread.start()

    print(f"[retak-mesh] callsign: {config.callsign}")
    print(f"[retak-mesh] ATAK UDP: {config.atak_host}:{config.atak_port}")
    print(f"[retak-mesh] RNode:    {config.rnode_port or 'not detected'}")
    print(f"[retak-mesh] Freq:     {config.rnode_freq}")
    print("[retak-mesh] running (Ctrl-C to stop)")

    def cleanup(sig, frame):
        print("\n[retak-mesh] shutting down...")
        mesh.stop()
        listener.stop()
        injector.stop()
        sys.exit(0)

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    threading.Event().wait()


if __name__ == "__main__":
    main()
