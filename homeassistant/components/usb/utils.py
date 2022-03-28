"""The USB Discovery integration."""
from __future__ import annotations

from typing import TYPE_CHECKING, cast

from serial.tools.list_ports_common import ListPortInfo

from .models import USBDevice

if TYPE_CHECKING:
    from pyudev.device import Attributes


def usb_device_from_port(port: ListPortInfo) -> USBDevice:
    """Convert serial ListPortInfo to USBDevice."""
    return USBDevice(
        device=port.device,
        vid=f"{hex(port.vid)[2:]:0>4}".upper(),
        pid=f"{hex(port.pid)[2:]:0>4}".upper(),
        serial_number=port.serial_number,
        manufacturer=port.manufacturer,
        description=port.description,
    )


def usb_device_from_attributes(attrs: Attributes) -> USBDevice | None:
    device = USBDevice(
        device=cast(bytes, attrs.get("device", b"")).decode(),
        vid=cast(bytes, attrs.get("idVendor", b"")).decode().upper(),
        pid=cast(bytes, attrs.get("idProduct", b"")).decode().upper(),
        serial_number=None,  # TODO iSerial + getString? or do we get "<N> <SERIAL>" here already?
        manufacturer=cast(bytes, attrs.get("manufacturer", b"")).decode() or None,
        description=cast(bytes, attrs.get("product", b"")).decode() or None,
    )
    if device.vid and device.pid:  # TODO and device.device
        return device
    return None
