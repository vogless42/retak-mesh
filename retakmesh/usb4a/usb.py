# usb4a.usb shim — returns a fake USB device so RNodeInterface creates a pyserial connection to the PTY


class FakeUsbDevice:
    def getVendorId(self):
        return 0x0403  # FTDI — will use default buffer params

    def getProductId(self):
        return 0x6001

    def getDeviceName(self):
        return None

    def getManufacturerName(self):
        return None

    def getProductName(self):
        return None


_fake_device = FakeUsbDevice()


def get_usb_device(device_name):
    return _fake_device


def get_usb_device_list():
    return [_fake_device]


def has_usb_permission(usb_device):
    return True


def request_usb_permission(usb_device):
    pass


class USBError(IOError):
    pass
