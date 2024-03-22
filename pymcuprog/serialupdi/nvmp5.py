"""
NVM controller implementation for P:5.

Present on, for example, AVR EB
"""
from logging import getLogger
from .nvm import NvmUpdi
from .timeout import Timeout
from ..pymcuprog_errors import PymcuprogSerialUpdiNvmTimeout, PymcuprogSerialUpdiNvmError

class NvmUpdiP5(NvmUpdi):
    """
    Version P:5 UPDI NVM properties
    """

    # NVM CTRL peripheral definition
    NVMCTRL_CTRLA = 0x00
    NVMCTRL_CTRLB = 0x01
    NVMCTRL_CTRLC = 0x02
    NVMCTRL_INTCTRL = 0x04
    NVMCTRL_INTFLAGS = 0x05
    NVMCTRL_STATUS = 0x06
    NVMCTRL_DATA = 0x08 # 16-bit
    NVMCTRL_ADDR = 0x0C # 24-bit

    # CTRLA commands
    NVMCMD_NOCMD = 0x00
    NVMCMD_NOOP = 0x01
    NVMCMD_FLASH_PAGE_WRITE = 0x04
    NVMCMD_FLASH_PAGE_ERASE_WRITE = 0x05
    NVMCMD_FLASH_PAGE_ERASE = 0x08
    NVMCMD_FLASH_PAGE_BUFFER_CLEAR = 0x0F
    NVMCMD_EEPROM_PAGE_WRITE = 0x14
    NVMCMD_EEPROM_PAGE_ERASE_WRITE = 0x15
    NVMCMD_EEPROM_PAGE_ERASE = 0x17
    NVMCMD_EEPROM_PAGE_BUFFER_CLEAR = 0x1F
    NVMCMD_CHIP_ERASE = 0x20
    NVMCMD_EEPROM_ERASE = 0x30

    # STATUS
    STATUS_WRITE_ERROR_bm = 0x70
    STATUS_WRITE_ERROR_bp = 4
    STATUS_EEPROM_BUSY_bp = 0
    STATUS_FLASH_BUSY_bp = 1


    def __init__(self, readwrite, device):
        NvmUpdi.__init__(self, readwrite, device)
        self.logger = getLogger(__name__)

    def chip_erase(self):
        """
        Does a chip erase using the NVM controller

        Note that on locked devices this is not possible and the ERASE KEY has to be used instead, see the unlock method
        """
        self.logger.debug("Chip erase using NVM CTRL")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready before chip erase")

        # Erase
        self.execute_nvm_command(self.NVMCMD_CHIP_ERASE)

        # And wait for it
        status = self.wait_nvm_ready()

        # Remove command
        self.execute_nvm_command(self.NVMCMD_NOCMD)

        if not status:
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready after chip erase")


    def erase_flash_page(self, address):
        """
        Erasing single flash page using the NVM controller

        :param address: Start address of page to erase
        :type address: int
        """
        self.logger.debug("Erase flash page at address 0x%08X", address)

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready before flash page erase")

        # Dummy write
        self.readwrite.write_data(address, [0xFF])

        # Erase
        self.execute_nvm_command(self.NVMCMD_FLASH_PAGE_ERASE)

        # And wait for it
        status = self.wait_nvm_ready()

        # Remove command
        self.execute_nvm_command(self.NVMCMD_NOCMD)

        if not status:
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready after flash page erase")

    def erase_eeprom(self):
        """
        Erase EEPROM memory only
        """
        self.logger.debug("Erase EEPROM")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready before EEPROM erase")

        # Erase
        self.execute_nvm_command(self.NVMCMD_EEPROM_ERASE)

        # And wait for it
        status = self.wait_nvm_ready()

        # Remove command
        self.execute_nvm_command(self.NVMCMD_NOCMD)

        if not status:
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready after EEPROM erase")

    def erase_user_row(self, address, size=0):
        """
        Erase User Row memory only

        :param address: Start address of user row
        :type address: int
        :param size: Size of user row
        :type size: int, optional, not used for this variant
        """
        self.logger.debug("Erase user row")

        # size is not used for this NVM version
        _dummy = size
        # On this NVM version user row is implemented as FLASH
        return self.erase_flash_page(address)

    def write_flash(self, address, data):
        """
        Writes data to flash

        :param address: address to write to
        :type address: int
        :param data: data to write
        :type data: list of bytes
        """
        return self.write_nvm(address, data, use_word_access=True)

    def write_user_row(self, address, data):
        """
        Writes data to user row

        :param address: address to write to
        :type address: int
        :param data: data to write
        :type data: list of bytes
        """
        # On this NVM variant user row is implemented as FLASH
        return self.write_nvm(address, data, use_word_access=True)

    def write_eeprom(self, address, data):
        """
        Write data to EEPROM

        :param address: address to write to
        :type address: int
        :param data: data to write
        :type data: list of bytes
        """
        return self.write_nvm(address, data, use_word_access=False,
                              nvmcommand=self.NVMCMD_EEPROM_PAGE_ERASE_WRITE,
                              erasebuffer_command=self.NVMCMD_EEPROM_PAGE_BUFFER_CLEAR)

    def write_fuse(self, address, data):
        """
        Writes one fuse value

        :param address: address to write to
        :type address: int
        :param data: data to write
        :type data: list of bytes
        """
        return self.write_eeprom(address, data)

    def write_nvm(self,
                  address,
                  data,
                  use_word_access,
                  nvmcommand=NVMCMD_FLASH_PAGE_WRITE,
                  erasebuffer_command=NVMCMD_FLASH_PAGE_BUFFER_CLEAR):
        """
        Writes a page of data to NVM

        By default the PAGE_WRITE command is used, which requires that the page is already erased.
        By default word access is used (required for flash)

        :param address: address to write to
        :type address: int
        :param data: data to write
        :type data: list of bytes
        :param use_word_access: True for 16-bit writes (eg: flash)
        :type use_word_access: bool, defaults to True
        :param nvmcommand: command to use for commit
        :type nvmcommand: int, defaults to NVMCMD_PAGE_WRITE
        :param erasebuffer_command: command to use for erasing the page buffer
        :type erasebuffer_command: int, defaults to NVMCMD_FLASH_PAGE_BUFFER_CLEAR
        :raises: PymcuprogSerialUpdiNvmTimeout if a timeout occurred
        :raises: PymcuprogSerialUpdiNvmError if an error condition is encountered
        """

        # Check that NVM controller is ready
        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready before page buffer clear")

        # Clear the page buffer
        self.logger.debug("Clear page buffer")
        self.execute_nvm_command(erasebuffer_command)

        # Wait for NVM controller to be ready
        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready after page buffer clear")

        # Load the page buffer by writing directly to location
        if use_word_access:
            self.readwrite.write_data_words(address, data)
        else:
            self.readwrite.write_data(address, data)

        # Write the page to NVM, maybe erase first
        self.logger.debug("Committing data")
        self.execute_nvm_command(nvmcommand)

        # Wait for NVM controller to be ready again
        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready after page write")

        # Remove command
        self.execute_nvm_command(self.NVMCMD_NOCMD)

    def wait_nvm_ready(self, timeout_ms=100):
        """
        Waits for the NVM controller to be ready

        :param timeout_ms: Timeout period in milliseconds
        :type timeout_ms: int, defaults to 100
        :returns: True if 'ready', False if timeout occurred before ready
        :rtype: bool
        :raises: PymcuprogSerialUpdiNvmError if an error condition is encountered
        """
        timeout = Timeout(timeout_ms)

        self.logger.debug("Wait NVM ready")
        while not timeout.expired():
            status = self.readwrite.read_byte(self.device.nvmctrl_address + self.NVMCTRL_STATUS)
            if status & self.STATUS_WRITE_ERROR_bm:
                self.logger.error("NVM error (%d)", status >> self.STATUS_WRITE_ERROR_bp)
                raise PymcuprogSerialUpdiNvmError(msg="NVM error", code=(status >> self.STATUS_WRITE_ERROR_bp))

            if not status & ((1 << self.STATUS_EEPROM_BUSY_bp) | (1 << self.STATUS_FLASH_BUSY_bp)):
                return True

        self.logger.error("Wait NVM ready timed out")
        return False

    def execute_nvm_command(self, command):
        """
        Executes an NVM COMMAND on the NVM CTRL

        :param command: command to execute
        :type param: int
        """
        self.logger.debug("NVMCMD %d executing", command)
        return self.readwrite.write_byte(self.device.nvmctrl_address + self.NVMCTRL_CTRLA, command)
