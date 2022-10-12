"""
Required device info for the ATxmega128A1U device
Note: this model is incomplete and is for Microchip internal regression test purposes only
"""

from pymcuprog.deviceinfo.eraseflags import ChiperaseEffect

DEVICE_INFO = {
    'name': 'atxmega128a1u',
    'architecture': 'xmega',

    # flash
    'flash_address_byte': 0x00800000,
    'flash_size_bytes': 0x22000,
    'flash_page_size_bytes': 512,
    'flash_read_size_bytes': 2,
    'flash_write_size_bytes': 512,
    'flash_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'flash_isolated_erase': True,

    # eeprom
    'eeprom_address_byte': 0x008C0000,
    'eeprom_size_bytes': 0x0800,
    'eeprom_page_size_bytes': 0x20,
    'eeprom_read_size_bytes': 1,
    'eeprom_write_size_bytes': 1,
    'eeprom_chiperase_effect': ChiperaseEffect.CONDITIONALLY_ERASED_AVR,
    'eeprom_isolated_erase': True,

    # Some extra AVR specific fields
    'nvmctrl_base': 0x00001000,
    'syscfg_base': 0x00000F00,
    'ocd_base': 0x0F80,
    'data_space_base': 0x0090,
    'interface': 'pdi+jtag',
    'address_size': '16-bit',
    'prog_clock_khz': 4000,
    'device_id': 0x1E974C,
}
