
"""
Required device info for the ATtiny104 device
Note: this model is incomplete and is for Microchip internal regression test purposes only
"""

from pymcuprog.deviceinfo.eraseflags import ChiperaseEffect

DEVICE_INFO = {
    'interface': 'TPI',
    'name': 'attiny104',
    'architecture': 'avrtinytiny',

    # Some extra AVR specific fields
    'device_id': 0x1E900B,
}
