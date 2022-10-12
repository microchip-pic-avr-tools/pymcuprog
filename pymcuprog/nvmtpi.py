"""
TPI/tinytiny NVM implementation
NB: This is a stub - not all features are implemented
"""
from pyedbglib.util import binary
from pyedbglib.protocols.tpiprotocol import TpiProtocol
from .nvm import NvmAccessProviderCmsisDapAvr

class NvmAccessProviderCmsisDapTpi(NvmAccessProviderCmsisDapAvr):
    """
    NVM Access the TPI way
    """

    def __init__(self, transport, device_info):
        NvmAccessProviderCmsisDapAvr.__init__(self, device_info)

        self._log_incomplete_stack('AVR-TPI')
        self.avr = TpiProtocol(transport)
        self.avr.enter_progmode()

    def __del__(self):
        pass

    def stop(self):
        """
        Stop programming session
        """
        self.logger.info("TPI-specific de-initialiser")
        self.avr.leave_progmode()

    def read_device_id(self):
        """
        Read the device ID

        :returns: Device ID raw bytes (little endian)
        """
        sig = self.avr.read_memory(TpiProtocol.XPRG_MEM_TYPE_APPL, 0x3FC0, 3)
        device_id_read = binary.unpack_be24(sig)
        self.logger.info("Device ID: '%06X'", device_id_read)
        return bytearray([sig[2], sig[1], sig[0]])

    def erase(self, memory_info=None, address=None):
        """
        Do a chip erase of the device
        """
        _dummy = memory_info
        _dummy = address
        raise NotImplementedError("NVM erase is not supported for TPI stack")

    @staticmethod
    def write(memory_info, offset, data):
        """
        Write the memory with data

        :param memory_info: dictionary for the memory as provided by the DeviceMemoryInfo class
        :param offset: relative offset within the memory type
        :param data: the data to program
        """
        _dummy = memory_info
        _dummy = offset
        _dummy = data
        raise NotImplementedError("NVM write is not supported for TPI stack")

    def read(self, memory_info, offset, numbytes):
        """
        Read the memory in chunks

        :param memory_info: dictionary for the memory as provided by the DeviceMemoryInfo class
        :param offset: relative offset in the memory type
        :param numbytes: number of bytes to read
        :return: array of bytes read
        """
        raise NotImplementedError("NVM read is not supported for TPI stack")
