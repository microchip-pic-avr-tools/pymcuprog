"""
Required device info for the PIC18F56Q71 devices
"""
from pymcuprog.deviceinfo.eraseflags import ChiperaseEffect

DEVICE_INFO = {
    'name': 'pic18f56q71',
    'architecture': 'PIC18',
    'device_id': 0x7760,
    # This device does not use an address as parameter for the bulk erase

    # Flash
    'flash_address_byte': 0,
    'flash_size_bytes': 64*1024,
    'flash_erase_size_words': 128,  # Sector erase
    'flash_page_size_words': 1,  # No page buffer
    'flash_write_size_words': 1,
    'flash_read_size_words': 1,
    'flash_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'flash_isolated_erase': False,

    # User ID
    'user_id_address_byte': 0x200000,
    'user_id_size_words': 32,
    'user_id_page_size_words': 1,
    'user_id_write_size_words': 1,
    'user_id_read_size_words': 1,
    'user_id_erase_address_byte': 0x300000,  # not used kept for compatibility
    'user_id_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'user_id_isolated_erase': False,

    # Config bytes
    'config_words_address_byte': 0x300000,
    'config_words_size_bytes': 11,
    'config_words_page_size_bytes': 1,
    'config_words_write_size_bytes': 1,
    'config_words_read_size_bytes': 1,
    'config_words_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'config_words_isolated_erase': False,

    # EEPROM
    'eeprom_address_byte': 0x380000,
    'eeprom_size_bytes': 256,
    'eeprom_page_size_bytes': 1,
    'eeprom_write_size_bytes': 1,
    'eeprom_read_size_bytes': 1,
    'eeprom_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'eeprom_isolated_erase': False,

    # ICD memory
    'icd_address_byte': 0x240000,
    'icd_size_bytes': 128*4*2, # 1KiB
    'icd_page_size_words': 128,# No page buffer so this is for sector erase
    'icd_write_size_words': 1,
    'icd_read_size_words': 1,
    'icd_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'icd_isolated_erase': False,

    # DIA
    'dia_address_byte': 0x2C0000,
    'dia_size_bytes': 60,
    'dia_page_size_bytes': 1,
    'dia_write_size_bytes': 0,
    'dia_read_size_bytes': 1,
    'dia_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'dia_isolated_erase': False,

    # DCI
    'dci_address_byte': 0x3C0000,
    'dci_size_bytes': 10,
    'dci_page_size_bytes': 1,
    'dci_write_size_bytes': 0,
    'dci_read_size_bytes': 1,
    'dci_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'dci_isolated_erase': False,
}
