"""
NVM implementations on various UPDI device families
"""
from logging import getLogger
from pymcuprog.pymcuprog_errors import PymcuprogError
from . import constants
from .timeout import Timeout


class NvmUpdi(object):
    """
    Base class for NVM
    """

    def __init__(self, readwrite, device):
        self.logger = getLogger(__name__)
        self.readwrite = readwrite
        self.device = device

    def chip_erase(self):
        """
        Does a chip erase using the NVM controller
        """
        raise NotImplementedError("NVM stack not ready")

    def erase_flash_page(self, address):
        """
        Erasing single flash page using the NVM controller

        :param address: Start address of page to erase
        :type address: int
        """
        raise NotImplementedError("NVM stack not ready")

    def erase_eeprom(self):
        """
        Erase EEPROM memory only
        """
        raise NotImplementedError("NVM stack not ready")

    def erase_user_row(self, address, size):
        """
        Erase User Row memory only

        :param address: Start address of user row
        :type address: int
        :param size: Size of user row
        :type size: int
        """
        raise NotImplementedError("NVM stack not ready")

    def write_flash(self, address, data):
        """
        Writes data to flash

        :param address: address to write to
        :param data: data to write
        """
        raise NotImplementedError("NVM stack not ready")

    def write_user_row(self, address, data):
        """
        Writes data to user row

        :param address: address to write to
        :param data: data to write
        """
        raise NotImplementedError("NVM stack not ready")

    def write_eeprom(self, address, data):
        """
        Write data to EEPROM

        :param address: address to write to
        :param data: data to write
        """
        raise NotImplementedError("NVM stack not ready")

    def write_fuse(self, address, data):
        """
        Writes one fuse value

        :param address: address to write to
        :param data: data to write
        """
        raise NotImplementedError("NVM stack not ready")

    def wait_nvm_ready(self):
        """
        Waits for the NVM controller to be ready
        """
        timeout = Timeout(10000)  # 10 sec timeout, just to be sure

        self.logger.debug("Wait NVM ready")
        while not timeout.expired():
            status = self.readwrite.read_byte(self.device.nvmctrl_address + constants.UPDI_NVMCTRL_STATUS)
            if status & (1 << constants.UPDI_NVM_STATUS_WRITE_ERROR):
                self.logger.error("NVM error")
                return False

            if not status & ((1 << constants.UPDI_NVM_STATUS_EEPROM_BUSY) |
                             (1 << constants.UPDI_NVM_STATUS_FLASH_BUSY)):
                return True

        self.logger.error("Wait NVM ready timed out")
        return False

    def execute_nvm_command(self, command):
        """
        Executes an NVM COMMAND on the NVM CTRL

        :param command: command to execute
        """
        self.logger.debug("NVMCMD %d executing", command)
        return self.readwrite.write_byte(self.device.nvmctrl_address + constants.UPDI_NVMCTRL_CTRLA, command)


class NvmUpdiV0(NvmUpdi):
    """
    AKA Version 0 UPDI NVM
    Present on, for example, tiny817 -> mega4809
    """

    def __init__(self, readwrite, device):
        NvmUpdi.__init__(self, readwrite, device)
        self.logger = getLogger(__name__)

    def chip_erase(self):
        """
        Does a chip erase using the NVM controller

        Note that on locked devices this is not possible
        and the ERASE KEY has to be used instead, see the unlock method
        """
        self.logger.info("Chip erase using NVM CTRL")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready before chip erase")

        # Erase
        self.execute_nvm_command(constants.UPDI_V0_NVMCTRL_CTRLA_CHIP_ERASE)

        # And wait for it
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready after chip erase")

        return True

    def erase_flash_page(self, address):
        """
        Erasing single flash page using the NVM controller (v0)

        :param address: Start address of page to erase
        :type address: int
        """
        self.logger.info("Erase flash page at address 0x%08X", address)

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready before flash page erase")

        # Dummy write
        self.readwrite.write_data(address, [0xFF])

        # Erase
        self.execute_nvm_command(constants.UPDI_V0_NVMCTRL_CTRLA_ERASE_PAGE)

        # And wait for it
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready after flash page erase")

    def erase_eeprom(self):
        """
        Erase EEPROM memory only (v0)
        """
        self.logger.info("Erase EEPROM")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready before EEPROM erase")

        # Erase
        self.execute_nvm_command(constants.UPDI_V0_NVMCTRL_CTRLA_ERASE_EEPROM)

        # And wait for it
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready after EEPROM erase")

    def erase_user_row(self, address, size):
        """
        Erase User Row memory only (v0)

        :param address: Start address of user row
        :type address: int
        """
        self.logger.info("Erase user row")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready before user row erase")

        # On this NVM version user row is implemented as EEPROM
        # When erasing single EEPROM pages a dummy write is needed for each location to be erased
        for offset in range(size):
            self.readwrite.write_data(address+offset, [0xFF])

        # Erase
        self.execute_nvm_command(constants.UPDI_V0_NVMCTRL_CTRLA_ERASE_PAGE)

        # And wait for it
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready after user row erase")


    def write_flash(self, address, data):
        """
        Writes data to flash (v0)

        :param address: address to write to
        :param data: data to write
        """
        return self.write_nvm(address, data, use_word_access=True)

    def write_user_row(self, address, data):
        """
        Writes data to user row (v0)

        :param address: address to write to
        :param data: data to write
        """
        # On this NVM variant user row is implemented as EEPROM
        return self.write_eeprom(address, data)

    def write_eeprom(self, address, data):
        """
        Write data to EEPROM (v0)

        :param address: address to write to
        :param data: data to write
        """
        return self.write_nvm(address, data, use_word_access=False,
                              nvmcommand=constants.UPDI_V0_NVMCTRL_CTRLA_ERASE_WRITE_PAGE)

    def write_fuse(self, address, data):
        """
        Writes one fuse value (v0)

        :param address: address to write to
        :param data: data to write
        """

        # Check that NVM controller is ready
        if not self.wait_nvm_ready():
            raise PymcuprogError("Timeout waiting for NVM controller to be ready before fuse write")

        # Write address to NVMCTRL ADDR
        self.logger.debug("Load NVM address")
        self.readwrite.write_byte(self.device.nvmctrl_address + constants.UPDI_NVMCTRL_ADDRL, address & 0xFF)
        self.readwrite.write_byte(self.device.nvmctrl_address + constants.UPDI_NVMCTRL_ADDRH, (address >> 8) & 0xFF)

        # Write data
        self.logger.debug("Load fuse data")
        self.readwrite.write_byte(self.device.nvmctrl_address + constants.UPDI_NVMCTRL_DATAL, data[0] & 0xFF)

        # Execute
        self.logger.debug("Execute fuse write")
        self.execute_nvm_command(constants.UPDI_V0_NVMCTRL_CTRLA_WRITE_FUSE)

        if not self.wait_nvm_ready():
            raise PymcuprogError("Timeout waiting for NVM controller to be ready after fuse write")

    def write_nvm(self, address, data, use_word_access, nvmcommand=constants.UPDI_V0_NVMCTRL_CTRLA_WRITE_PAGE):
        """
        Writes a page of data to NVM (v0)

        By default the PAGE_WRITE command is used, which
        requires that the page is already erased.
        By default word access is used (flash)

        :param address: address to write to
        :param data: data to write
        :param use_word_access: write whole words?
        :param nvmcommand: command to use for commit
        """

        # Check that NVM controller is ready
        if not self.wait_nvm_ready():
            raise PymcuprogError("Timeout waiting for NVM controller to be ready before page buffer clear")

        # Clear the page buffer
        self.logger.debug("Clear page buffer")
        self.execute_nvm_command(constants.UPDI_V0_NVMCTRL_CTRLA_PAGE_BUFFER_CLR)

        # Wait for NVM controller to be ready
        if not self.wait_nvm_ready():
            raise PymcuprogError("Timeout waiting for NVM controller to be ready after page buffer clear")

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
            raise PymcuprogError("Timeout waiting for NVM controller to be ready after page write")


class NvmUpdiAvrV2(NvmUpdi):
    """
    AKA Version 2 UPDI NVM
    Present on, for example, AVR-DA and newer
    """

    def __init__(self, readwrite, device):
        NvmUpdi.__init__(self, readwrite, device)
        self.logger = getLogger(__name__)

    def chip_erase(self):
        """
        Does a chip erase using the NVM controller
        Note that on locked devices this it not possible
        and the ERASE KEY has to be used instead
        """
        self.logger.info("Chip erase using NVM CTRL")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise Exception("Timeout waiting for NVM controller to be ready before chip erase")

        # Erase
        self.execute_nvm_command(constants.UPDI_V2_NVMCTRL_CTRLA_CHIP_ERASE)

        # And wait for it
        if not self.wait_nvm_ready():
            raise Exception("Timeout waiting for NVM controller to be ready after chip erase")

        return True

    def erase_flash_page(self, address):
        """
        Erasing single flash page using the NVM controller (v1)

        :param address: Start address of page to erase
        :type address: int
        """
        self.logger.info("Erase flash page at address 0x%08X", address)

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready before flash page erase")

        # Erase command
        self.execute_nvm_command(constants.UPDI_V2_NVMCTRL_CTRLA_FLASH_PAGE_ERASE)

        # Dummy write
        self.readwrite.write_data(address, [0xFF])

        # And wait for it
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready after flash page erase")

        # Remove command from NVM controller
        self.logger.debug("Clear NVM command")
        self.execute_nvm_command(constants.UPDI_V2_NVMCTRL_CTRLA_NOCMD)

    def erase_eeprom(self):
        """
        Erase EEPROM memory only (v1)
        """
        self.logger.info("Erase EEPROM")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready before EEPROM erase")

        # Erase
        self.execute_nvm_command(constants.UPDI_V2_NVMCTRL_CTRLA_EEPROM_ERASE)

        # And wait for it
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready after EEPROM erase")

        # Remove command from NVM controller
        self.logger.debug("Clear NVM command")
        self.execute_nvm_command(constants.UPDI_V2_NVMCTRL_CTRLA_NOCMD)

    def erase_user_row(self, address, size):
        """
        Erase User Row memory only (v1)

        :param address: Start address of user row
        :type address: int
        """
        # size is not used for this NVM version
        _dummy = size
        # On this NVM version user row is implemented as flash
        return self.erase_flash_page(address)

    def write_flash(self, address, data):
        """
        Writes data to flash (v1)

        :param address: address to write to
        :param data: data to write
        """
        return self.write_nvm(address, data, use_word_access=True)

    def write_user_row(self, address, data):
        """
        Writes data to user row (v1)

        :param address: address to write to
        :param data: data to write
        """
        # On this NVM variant user row is implemented as Flash
        return self.write_nvm(address, data, use_word_access=False)

    def write_eeprom(self, address, data):
        """
        Writes data to NVM (EEPROM)

        :param address: address to write to
        :param data: data to write
        """
        nvm_command = constants.UPDI_V2_NVMCTRL_CTRLA_EEPROM_ERASE_WRITE

        # Check that NVM controller is ready
        if not self.wait_nvm_ready():
            raise Exception("Timeout waiting for NVM ready before command write")

        # Write the command to the NVM controller
        self.logger.info("NVM EEPROM erase/write command")
        self.execute_nvm_command(nvm_command)

        # Write the data
        self.readwrite.write_data(address, data)

        # Wait for NVM controller to be ready again
        if not self.wait_nvm_ready():
            raise Exception("Timeout waiting for NVM ready after data write")

        # Remove command from NVM controller
        self.logger.info("Clear NVM command")
        self.execute_nvm_command(constants.UPDI_V2_NVMCTRL_CTRLA_NOCMD)

    def write_fuse(self, address, data):
        """
        Writes one fuse value
        V1 fuses are EEPROM-based

        :param address: address to write to
        :param data: data to write
        """
        return self.write_eeprom(address, data)

    def write_nvm(self, address, data, use_word_access):
        """
        Writes data to NVM (version 1)
        This version of the NVM block has no page buffer, so words are written directly.

        :param address: address to write to
        :param data: data to write
        :param use_word_access: write in whole words?
        """
        nvm_command = constants.UPDI_V2_NVMCTRL_CTRLA_FLASH_WRITE

        # Check that NVM controller is ready
        if not self.wait_nvm_ready():
            raise Exception("Timeout waiting for NVM controller to be ready before page buffer clear")

        # Write the command to the NVM controller
        self.logger.info("NVM write command")
        self.execute_nvm_command(nvm_command)

        # Write the data
        if use_word_access:
            self.readwrite.write_data_words(address, data)
        else:
            self.readwrite.write_data(address, data)

        # Wait for NVM controller to be ready again
        if not self.wait_nvm_ready():
            raise Exception("Timeout waiting for NVM controller to be ready after data write")

        # Remove command from NVM controller
        self.logger.info("Clear NVM command")
        self.execute_nvm_command(constants.UPDI_V2_NVMCTRL_CTRLA_NOCMD)

class NvmUpdiAvrV3(NvmUpdi):
    """
    AKA Version 3 UPDI NVM
    Present on, for example, AVR-EA
    """

    def __init__(self, readwrite, device):
        NvmUpdi.__init__(self, readwrite, device)
        self.logger = getLogger(__name__)

    def chip_erase(self):
        """
        Does a chip erase using the NVM controller

        Note that on locked devices this is not possible
        and the ERASE KEY has to be used instead, see the unlock method
        """
        self.logger.info("Chip erase using NVM CTRL")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready before chip erase")

        # Erase
        self.execute_nvm_command(constants.UPDI_V3_NVMCTRL_CTRLA_CHIP_ERASE)

        # And wait for it
        status = self.wait_nvm_ready()

        # Remove command
        self.execute_nvm_command(constants.UPDI_V3_NVMCTRL_CTRLA_NOCMD)

        if not status:
            raise IOError("Timeout waiting for NVM controller to be ready after chip erase")

        return True

    def erase_flash_page(self, address):
        """
        Erasing single flash page using the NVM controller (v3)

        :param address: Start address of page to erase
        :type address: int
        """
        self.logger.info("Erase flash page at address 0x%08X", address)

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready before flash page erase")

        # Dummy write
        self.readwrite.write_data(address, [0xFF])

        # Erase
        self.execute_nvm_command(constants.UPDI_V3_NVMCTRL_CTRLA_FLASH_PAGE_ERASE)

        # And wait for it
        status = self.wait_nvm_ready()

        # Remove command
        self.execute_nvm_command(constants.UPDI_V3_NVMCTRL_CTRLA_NOCMD)

        if not status:
            raise IOError("Timeout waiting for NVM controller to be ready after flash page erase")

    def erase_eeprom(self):
        """
        Erase EEPROM memory only
        """
        self.logger.info("Erase EEPROM")

        # Wait until NVM CTRL is ready to erase
        if not self.wait_nvm_ready():
            raise IOError("Timeout waiting for NVM controller to be ready before EEPROM erase")

        # Erase
        self.execute_nvm_command(constants.UPDI_V3_NVMCTRL_CTRLA_EEPROM_ERASE)

        # And wait for it
        status = self.wait_nvm_ready()

        # Remove command
        self.execute_nvm_command(constants.UPDI_V3_NVMCTRL_CTRLA_NOCMD)

        if not status:
            raise IOError("Timeout waiting for NVM controller to be ready after EEPROM erase")

    def erase_user_row(self, address, size):
        """
        Erase User Row memory only

        :param address: Start address of user row
        :type address: int
        """
        self.logger.info("Erase user row")

        # On this NVM version user row is implemented as FLASH
        return self.erase_flash_page(self, address)

    def write_flash(self, address, data):
        """
        Writes data to flash (v3)

        :param address: address to write to
        :param data: data to write
        """
        return self.write_nvm(address, data, use_word_access=True)

    def write_user_row(self, address, data):
        """
        Writes data to user row (v3)

        :param address: address to write to
        :param data: data to write
        """
        # On this NVM variant user row is implemented as FLASH
        return self.write_nvm(address, data, use_word_access=True)

    def write_eeprom(self, address, data):
        """
        Write data to EEPROM (v3)

        :param address: address to write to
        :param data: data to write
        """
        return self.write_nvm(address, data, use_word_access=False,
                              nvmcommand=constants.UPDI_V3_NVMCTRL_CTRLA_EEPROM_PAGE_ERASE_WRITE)

    def write_fuse(self, address, data):
        """
        Writes one fuse value (v3)

        :param address: address to write to
        :param data: data to write
        """
        return self.write_eeprom(address, data)

    def write_nvm(self, address, data, use_word_access, nvmcommand=constants.UPDI_V3_NVMCTRL_CTRLA_FLASH_PAGE_WRITE):
        """
        Writes a page of data to NVM (v3)

        By default the PAGE_WRITE command is used, which
        requires that the page is already erased.
        By default word access is used (flash)

        :param address: address to write to
        :param data: data to write
        :param use_word_access: write whole words?
        :param nvmcommand: command to use for commit
        """

        # Check that NVM controller is ready
        if not self.wait_nvm_ready():
            raise PymcuprogError("Timeout waiting for NVM controller to be ready before page buffer clear")

        # Clear the page buffer
        self.logger.debug("Clear page buffer")
        self.execute_nvm_command(constants.UPDI_V3_NVMCTRL_CTRLA_FLASH_PAGE_BUFFER_CLEAR)

        # Wait for NVM controller to be ready
        if not self.wait_nvm_ready():
            raise PymcuprogError("Timeout waiting for NVM controller to be ready after page buffer clear")

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
            raise PymcuprogError("Timeout waiting for NVM controller to be ready after page write")

        # Remove command
        self.execute_nvm_command(constants.UPDI_V3_NVMCTRL_CTRLA_NOCMD)
