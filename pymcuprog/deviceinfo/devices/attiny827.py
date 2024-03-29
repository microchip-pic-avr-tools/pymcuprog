
"""
Required device info for the attiny827 devices
The following data was collected from device pack Microchip.ATtiny_DFP 3.0.138
"""

from pymcuprog.deviceinfo.eraseflags import ChiperaseEffect

DEVICE_INFO = {
    'interface': 'UPDI',
    'name': 'attiny827',
    'architecture': 'avr8x',

    # eeprom
    'eeprom_address_byte': 0x00001400,
    'eeprom_size_bytes': 0x0080,
    'eeprom_page_size_bytes': 0x20,
    'eeprom_read_size_bytes': 0x01,
    'eeprom_write_size_bytes': 0x01,
    'eeprom_chiperase_effect': ChiperaseEffect.CONDITIONALLY_ERASED_AVR,
    'eeprom_isolated_erase': True,

    # flash
    'flash_address_byte': 0x00008000,
    'flash_size_bytes': 0x2000,
    'flash_page_size_bytes': 0x40,
    'flash_read_size_bytes': 0x02,
    'flash_write_size_bytes': 0x40,
    'flash_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'flash_isolated_erase': True,

    # fuses
    'fuses_address_byte': 0x1280,
    'fuses_size_bytes': 0x09,
    'fuses_page_size_bytes': 0x01,
    'fuses_read_size_bytes': 0x01,
    'fuses_write_size_bytes': 0x01,
    'fuses_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'fuses_isolated_erase': False,

    # internal_sram
    'internal_sram_address_byte': 0x3c00,
    'internal_sram_size_bytes': 0x0400,
    'internal_sram_page_size_bytes': 0x01,
    'internal_sram_read_size_bytes': 0x01,
    'internal_sram_write_size_bytes': 0x01,
    'internal_sram_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'internal_sram_isolated_erase': False,

    # lockbits
    'lockbits_address_byte': 0x0000128A,
    'lockbits_size_bytes': 0x1,
    'lockbits_page_size_bytes': 0x01,
    'lockbits_read_size_bytes': 0x01,
    'lockbits_write_size_bytes': 0x01,
    'lockbits_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'lockbits_isolated_erase': False,

    # signatures
    'signatures_address_byte': 0x1100,
    'signatures_size_bytes': 0x40,
    'signatures_page_size_bytes': 0x01,
    'signatures_read_size_bytes': 0x01,
    'signatures_write_size_bytes': 0x00,
    'signatures_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'signatures_isolated_erase': False,

    # user_row
    'user_row_address_byte': 0x1300,
    'user_row_size_bytes': 0x20,
    # user_row is implemented as EEPROM so writes should not be padded to start of page, i.e. set page size to 1
    'user_row_page_size_bytes': 0x01,
    'user_row_read_size_bytes': 0x01,
    'user_row_write_size_bytes': 0x01,
    'user_row_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'user_row_isolated_erase': True,

    # Some extra AVR specific fields
    'nvmctrl_base': 0x00001000,
    'syscfg_base': 0x00000F00,
    'ocd_base': 0x00000F80,
    'prog_clock_khz': 900,
    'address_size': '16-bit',
    'hv_implementation': 0,
    'device_id': 0x1E9327,

}
