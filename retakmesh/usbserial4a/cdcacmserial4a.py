# cdcacmserial4a shim — wraps pyserial for Reticulum Android RNodeInterface

from .serial4a import get_serial_port


class CdcAcmSerial:
    def __init__(self, port=None, baudrate=115200, bytesize=8, parity="N",
                 stopbits=1, timeout=None, xonxoff=False, rtscts=False,
                 dsrdtr=False, inter_byte_timeout=None, write_timeout=None):
        self._port = get_serial_port(
            port=port, baudrate=baudrate, bytesize=bytesize,
            parity=parity, stopbits=stopbits, timeout=timeout,
            xonxoff=xonxoff, rtscts=rtscts, dsrdtr=dsrdtr,
            inter_byte_timeout=inter_byte_timeout,
            write_timeout=write_timeout,
        )

    @property
    def is_open(self):
        return self._port.is_open

    def read(self, size=1):
        return self._port.read(size)

    def write(self, data):
        return self._port.write(data)

    def close(self):
        self._port.close()

    @property
    def in_waiting(self):
        return self._port.in_waiting
