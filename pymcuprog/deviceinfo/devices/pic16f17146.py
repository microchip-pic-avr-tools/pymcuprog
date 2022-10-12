"""
Required device info for the PIC16F17146 devices
"""
from pymcuprog.deviceinfo.eraseflags import ChiperaseEffect

DEVICE_INFO = {
    'name': 'pic16f17146',
    'architecture': 'PIC16',
    'device_id': 0x30E1,
    # This device does not use an address as parameter for the bulk erase

    # Flash
    'flash_address_word': 0,
    'flash_size_words': 16*1024,
    'flash_page_size_words': 32,
    'flash_write_size_words': 1,
    'flash_read_size_words': 1,
    'flash_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'flash_isolated_erase': False,

    # User ID
    'user_id_address_word': 0x8000,
    'user_id_size_words': 4,
    'user_id_page_size_words': 1,
    'user_id_write_size_words': 1,
    'user_id_read_size_words': 1,
    'user_id_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'user_id_isolated_erase': False,

    # Config words
    'config_words_address_word': 0x8007,
    'config_words_size_words': 5,
    'config_words_page_size_words': 1,
    'config_words_write_size_words': 1,
    'config_words_read_size_words': 1,
    'config_words_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'config_words_isolated_erase': False,

    # EEPROM
    'eeprom_address_word': 0xF000,
    'eeprom_size_bytes': 256,
    'eeprom_page_size_bytes': 1,
    'eeprom_write_size_bytes': 1,
    'eeprom_read_size_bytes': 1,
    'eeprom_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    'eeprom_isolated_erase': False,

    # ICD
    'icd_address_word': 0x8600,
    'icd_size_words': 512,
    'icd_page_size_words': 32,
    'icd_write_size_words': 1,
    'icd_read_size_words': 1,
    'icd_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'icd_isolated_erase': True,
}
