"""
NVM controller implementation for P:0.

Present on tiny0, 1, 2 and mega0 (eg: tiny817 -> mega4809)
"""
from logging import getLogger
from .nvm import NvmUpdi
from .timeout import Timeout
from ..pymcuprog_errors import PymcuprogSerialUpdiNvmTimeout, PymcuprogSerialUpdiNvmError

class NvmUpdiP0(NvmUpdi):
    """
    Version P:0 UPDI NVM properties
    """

    # NVM CTRL peripheral definition
    NVMCTRL_CTRLA = 0x00
    NVMCTRL_CTRLB = 0x01
    NVMCTRL_STATUS = 0x02
    NVMCTRL_INTCTRL = 0x03
    NVMCTRL_INTFLAGS = 0x04
    NVMCTRL_DATA = 0x06 # 16-bit
    NVMCTRL_ADDR = 0x08 # 16-bit

    # CTRLA commands
    NVMCMD_NOP = 0x00
    NVMCMD_WRITE_PAGE = 0x01
    NVMCMD_ERASE_PAGE = 0x02
    NVMCMD_ERASE_WRITE_PAGE = 0x03
    NVMCMD_PAGE_BUFFER_CLR = 0x04
    NVMCMD_CHIP_ERASE = 0x05
    NVMCMD_ERASE_EEPROM = 0x06
    NVMCMD_WRITE_FUSE = 0x07

    # STATUS
    STATUS_WRITE_ERROR_bp = 2
    STATUS_EEPROM_BUSY_bp = 1
    STATUS_FLASH_BUSY_bp = 0

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
        if not self.wait_nvm_ready():
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
        self.execute_nvm_command(self.NVMCMD_ERASE_PAGE)

        # And wait for it
        if not self.wait_nvm_ready():
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
        self.execute_nvm_command(self.NVMCMD_ERASE_EEPROM)

        # And wait for it
        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready after EEPROM erase")

    def erase_user_row(self, address, size):
        """
        Erase User Row memory only

        :param address: Start address of user row
        :type address: int
        :param size: Size of user row
        :type size: int
        """
        self.logger.debug("Erase user row")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready before user row erase")

        # On this NVM version user row is implemented as EEPROM
        # When erasing single EEPROM pages a dummy write is needed for each location to be erased
        for offset in range(size):
            self.readwrite.write_data(address+offset, [0xFF])

        # Erase
        self.execute_nvm_command(self.NVMCMD_ERASE_PAGE)

        # And wait for it
        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready after user row erase")


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
        # On this NVM variant user row is implemented as EEPROM
        return self.write_eeprom(address, data)

    def write_eeprom(self, address, data):
        """
        Write data to EEPROM

        :param address: address to write to
        :type address: int
        :param data: data to write
        :type data: list of bytes
        """
        return self.write_nvm(address, data, use_word_access=False, nvmcommand=self.NVMCMD_ERASE_WRITE_PAGE)

    def write_fuse(self, address, data):
        """
        Writes one fuse value

        :param address: address to write to
        :type address: int
        :param data: data to write
        :type data: list of bytes
        """

        # Check that NVM controller is ready
        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready before fuse write")

        # Write address to NVMCTRL ADDR
        self.logger.debug("Load NVM address")
        self.readwrite.write_byte(self.device.nvmctrl_address + self.NVMCTRL_ADDR, address & 0xFF)
        self.readwrite.write_byte(self.device.nvmctrl_address + self.NVMCTRL_ADDR+1, (address >> 8) & 0xFF)

        # Write data
        self.logger.debug("Load fuse data")
        self.readwrite.write_byte(self.device.nvmctrl_address + self.NVMCTRL_DATA, data[0] & 0xFF)

        # Execute
        self.logger.debug("Execute fuse write")
        self.execute_nvm_command(self.NVMCMD_WRITE_FUSE)

        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready after fuse write")

    def write_nvm(self, address, data, use_word_access=True, nvmcommand=NVMCMD_WRITE_PAGE):
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
        :raises: PymcuprogSerialUpdiNvmTimeout if a timeout occurred
        :raises: PymcuprogSerialUpdiNvmError if an error condition is encountered
        """

        # Check that NVM controller is ready
        if not self.wait_nvm_ready():
            raise PymcuprogSerialUpdiNvmTimeout("Timeout waiting for NVM controller to be ready before page buffer clear")

        # Clear the page buffer
        self.logger.debug("Clear page buffer")
        self.execute_nvm_command(self.NVMCMD_PAGE_BUFFER_CLR)

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
            if status & (1 << self.STATUS_WRITE_ERROR_bp):
                self.logger.error("NVM error")
                raise PymcuprogSerialUpdiNvmError(msg="NVM error", code=1)

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
