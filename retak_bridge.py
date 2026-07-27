import sys
import signal
import threading
import queue

from retakmesh.config import Config
from retakmesh.mesh import MeshInterface
from retakmesh.atak_listener import ATAKListener
from retakmesh.atak_injector import ATAKInjector


def main():
    config = Config()

    tx_queue = queue.Queue()
    rx_queue = queue.Queue()

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
