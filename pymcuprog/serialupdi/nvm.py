"""
NVM implementations on various UPDI device families
"""
from logging import getLogger

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
