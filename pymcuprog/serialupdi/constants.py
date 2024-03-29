"""
UPDI protocol constants
"""
# UPDI commands and control definitions
UPDI_BREAK = 0x00

UPDI_LDS = 0x00
UPDI_STS = 0x40
UPDI_LD = 0x20
UPDI_ST = 0x60
UPDI_LDCS = 0x80
UPDI_STCS = 0xC0
UPDI_REPEAT = 0xA0
UPDI_KEY = 0xE0

UPDI_PTR = 0x00
UPDI_PTR_INC = 0x04
UPDI_PTR_ADDRESS = 0x08

UPDI_ADDRESS_8 = 0x00
UPDI_ADDRESS_16 = 0x04
UPDI_ADDRESS_24 = 0x08

UPDI_DATA_8 = 0x00
UPDI_DATA_16 = 0x01
UPDI_DATA_24 = 0x02

UPDI_KEY_SIB = 0x04
UPDI_KEY_KEY = 0x00

UPDI_KEY_64 = 0x00
UPDI_KEY_128 = 0x01
UPDI_KEY_256 = 0x02

UPDI_SIB_8BYTES = UPDI_KEY_64
UPDI_SIB_16BYTES = UPDI_KEY_128
UPDI_SIB_32BYTES = UPDI_KEY_256

UPDI_REPEAT_BYTE = 0x00
UPDI_REPEAT_WORD = 0x01

UPDI_PHY_SYNC = 0x55
UPDI_PHY_ACK = 0x40

UPDI_MAX_REPEAT_SIZE = (0xFF+1) # Repeat counter of 1-byte, with off-by-one counting

# CS and ASI Register Address map
UPDI_CS_STATUSA = 0x00
UPDI_CS_STATUSB = 0x01
UPDI_CS_CTRLA = 0x02
UPDI_CS_CTRLB = 0x03
UPDI_ASI_KEY_STATUS = 0x07
UPDI_ASI_RESET_REQ = 0x08
UPDI_ASI_CTRLA = 0x09
UPDI_ASI_SYS_CTRLA = 0x0A
UPDI_ASI_SYS_STATUS = 0x0B
UPDI_ASI_CRC_STATUS = 0x0C

UPDI_CTRLA_IBDLY_BIT = 7
UPDI_CTRLA_RSD_BIT = 3

UPDI_CTRLB_CCDETDIS_BIT = 3
UPDI_CTRLB_UPDIDIS_BIT = 2

UPDI_KEY_NVM = b"NVMProg "
UPDI_KEY_CHIPERASE = b"NVMErase"
UPDI_KEY_UROW = b"NVMUs&te"

UPDI_ASI_STATUSA_REVID = 4
UPDI_ASI_STATUSB_PESIG = 0

UPDI_ASI_KEY_STATUS_CHIPERASE = 3
UPDI_ASI_KEY_STATUS_NVMPROG = 4
UPDI_ASI_KEY_STATUS_UROWWRITE = 5

UPDI_ASI_SYS_STATUS_RSTSYS = 5
UPDI_ASI_SYS_STATUS_INSLEEP = 4
UPDI_ASI_SYS_STATUS_NVMPROG = 3
UPDI_ASI_SYS_STATUS_UROWPROG = 2
UPDI_ASI_SYS_STATUS_LOCKSTATUS = 0

UPDI_ASI_SYS_CTRLA_UROW_FINAL = 1

UPDI_RESET_REQ_VALUE = 0x59
