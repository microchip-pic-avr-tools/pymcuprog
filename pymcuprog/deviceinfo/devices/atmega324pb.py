"""
Required device info for the ATmega324PB device
Note: this model is incomplete and is for Microchip internal regression test purposes only

"""
from pymcuprog.deviceinfo.eraseflags import ChiperaseEffect

DEVICE_INFO = {
    'name': 'atmega324pb',
    'architecture': 'avr8',

    # Flash
    'flash_address_byte': 0,
    'flash_size_bytes': 0x8000,
    'flash_page_size_bytes': 0x80,
    'flash_write_size_bytes': 0x80,
    'flash_read_size_bytes': 0x80,
    'flash_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'flash_isolated_erase': False,

    # eeprom
    'eeprom_address_byte': 0x0000,
    'eeprom_size_bytes': 0x0400,
    'eeprom_page_size_bytes': 0x04,
    'eeprom_read_size_bytes': 1,
    'eeprom_write_size_bytes': 1,
    'eeprom_chiperase_effect': ChiperaseEffect.CONDITIONALLY_ERASED_AVR,
    'eeprom_isolated_erase': False,

    # Some extra AVR specific fields
    'interface': 'jtag',
    'device_id': 0x1E9517,
}
