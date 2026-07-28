# usb4a.usb shim — always returns None for get_usb_device
# This prevents RNodeInterface from trying to use Android USB APIs on Termux


def get_usb_device(device_name):
    return None


def get_usb_device_list():
    return []


def has_usb_permission(usb_device):
    return False


def request_usb_permission(usb_device):
    pass


class USBError(IOError):
    pass
