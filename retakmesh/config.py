import os
import glob
import RNS

CONFIG_DIR = os.path.expanduser("~/.retakmesh")
IDENTITY_FILE = os.path.join(CONFIG_DIR, "identity")
RNS_CONFIG_DIR = os.path.join(CONFIG_DIR, "reticulum")
FREQ_FILE = os.path.join(CONFIG_DIR, "rnode_freq")

DEFAULT_ATAK_HOST = "239.2.3.1"
DEFAULT_ATAK_PORT = 6969
DEFAULT_RNODE_FREQ = 915000000


class Config:
    def __init__(self):
        self.atak_host = DEFAULT_ATAK_HOST
        self.atak_port = DEFAULT_ATAK_PORT
        self.rnode_port = None
        self.rnode_freq = DEFAULT_RNODE_FREQ
        self.callsign = None
        self.identity = None

        self._ensure_dirs()
        self._load_rnode_freq()
        self._load_or_create_identity()
        self._detect_rnode()
        self._generate_callsign()

    def _ensure_dirs(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        os.makedirs(RNS_CONFIG_DIR, exist_ok=True)

    def _load_rnode_freq(self):
        if os.path.exists(FREQ_FILE):
            try:
                with open(FREQ_FILE) as f:
                    val = f.read().strip()
                    self.rnode_freq = int(val)
            except (ValueError, OSError):
                pass

    def _load_or_create_identity(self):
        if os.path.exists(IDENTITY_FILE):
            with open(IDENTITY_FILE, "rb") as f:
                self.identity = RNS.Identity.from_bytes(f.read())
        else:
            self.identity = RNS.Identity()
            with open(IDENTITY_FILE, "wb") as f:
                f.write(self.identity.get_private_key())

    def _detect_rnode(self):
        for pattern in ["/dev/ttyUSB*", "/dev/ttyACM*"]:
            ports = sorted(glob.glob(pattern))
            if ports:
                self.rnode_port = ports[0]
                break

    def _generate_callsign(self):
        short = RNS.hexrep(self.identity.hash)[-4:]
        self.callsign = f"rnode-{short}"
