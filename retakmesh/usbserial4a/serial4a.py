# serial4a shim — wraps pyserial.Serial with the API Reticulum expects

import sys

_HAS_SERIAL = False
try:
    import serial as _serial
    _HAS_SERIAL = True
except ImportError:
    pass


class Serial:
    def __init__(self, port=None, baudrate=115200, bytesize=8, parity="N",
                 stopbits=1, timeout=None, xonxoff=False, rtscts=False,
                 dsrdtr=False, inter_byte_timeout=None, write_timeout=None):
        if not _HAS_SERIAL:
            raise ImportError(
                "pyserial is not installed. Run: pip install pyserial"
            )
        self._port = _serial.Serial(
            port=port, baudrate=baudrate, bytesize=bytesize,
            parity=parity, stopbits=stopbits, timeout=timeout,
            xonxoff=xonxoff, rtscts=rtscts, dsrdtr=dsrdtr,
            inter_byte_timeout=inter_byte_timeout,
            write_timeout=write_timeout,
        )
        self.DEFAULT_READ_BUFFER_SIZE = 4096
        self.USB_READ_TIMEOUT_MILLIS = 100
        self.USB_WRITE_TIMEOUT_MILLIS = 100
        self._timeout = timeout

    @property
    def is_open(self):
        return self._port.is_open

    @property
    def timeout(self):
        return self._timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value
        if hasattr(self, "_port") and self._port:
            self._port.timeout = value

    def read(self, size=1):
        return self._port.read(size)

    def write(self, data):
        return self._port.write(data)

    def close(self):
        self._port.close()

    @property
    def in_waiting(self):
        return self._port.in_waiting


def get_serial_port(port=None, baudrate=115200, bytesize=8, parity="N",
                    stopbits=1, timeout=None, xonxoff=False, rtscts=False,
                    dsrdtr=False, inter_byte_timeout=None, write_timeout=None):
    return Serial(
        port=port, baudrate=baudrate, bytesize=bytesize,
        parity=parity, stopbits=stopbits, timeout=timeout,
        xonxoff=xonxoff, rtscts=rtscts, dsrdtr=dsrdtr,
        inter_byte_timeout=inter_byte_timeout,
        write_timeout=write_timeout,
    )
