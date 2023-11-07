"""
Required device info for the dspic33ck64mc105 devices
"""
from pymcuprog.deviceinfo.eraseflags import ChiperaseEffect

DEVICE_INFO = {
    'name': 'dspic33ck64mc105',
    'device_id': 0x9912,
    'architecture': 'dsPIC33',
    'interface' : 'icsp',

    # Flash
    'flash_address_byte': 0,
    'flash_size_words': 0x00B000,
    'flash_page_size_bytes': 8, # This architecture has 2-word latches (6 packed bytes / 8 flat bytes)
    'flash_write_size_bytes': 8, # The GEN4 byte-code writes chunks of 6 packed bytes / 2 words / 8 flat bytes
    'flash_read_size_bytes': 16, # The GEN4 byte-code reads chunks of 12 packed bytes / 4 words / 16 flat bytes
    'flash_chiperase_effect': ChiperaseEffect.ALWAYS_ERASED,
    # Configuration words are integrated in the flash, but since they are not represented
    # as a separate memory it is correct to state that flash can be erased in isolation
    'flash_isolated_erase': True,

    # ICD memory
    'icd_address_byte': 0x800000 * 2,
    'icd_size_bytes': 512 * 16,  # 8KiB
    'icd_page_size_bytes': 8,
    'icd_write_size_bytes': 8,
    'icd_read_size_bytes': 16,
    'icd_chiperase_effect': ChiperaseEffect.NOT_ERASED,
    'icd_isolated_erase': True,
}
