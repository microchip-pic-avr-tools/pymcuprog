"""
XMEGA NVM implementation
NB: This is a stub - not all features are implemented
"""
from pyedbglib.protocols.jtagice3protocol import Jtagice3ResponseError
from pyedbglib.util import binary
from pyedbglib.protocols.avr8protocol import Avr8Protocol

from .nvm import NvmAccessProviderCmsisDapAvr
from .avr8target import XmegaAvrTarget

class NvmAccessProviderCmsisDapXmega(NvmAccessProviderCmsisDapAvr):
    """
    NVM Access the Xmega way
    """

    def __init__(self, transport, device_info):
        NvmAccessProviderCmsisDapAvr.__init__(self, device_info)

        self._log_incomplete_stack('AVR-xmega')
        self.avr = XmegaAvrTarget(transport)
        self.avr.setup_config(device_info)
        self.avr.setup_prog_session()

    def __del__(self):
        pass

    def start(self, user_interaction_callback=None):
        """
        Start (activate) session for XMEGA targets
        """
        self.logger.debug("XMEGA-specific initialiser")

        try:
            self.avr.activate_physical()
        except Jtagice3ResponseError as error:
            # The debugger could be out of sync with the target, retry
            if error.code == Avr8Protocol.AVR8_FAILURE_INVALID_PHYSICAL_STATE:
                self.logger.info("Physical state out of sync.  Retrying.")
                self.avr.deactivate_physical()
                self.avr.activate_physical()
            else:
                raise
        self.avr.enter_progmode()

    def stop(self):
        """
        Stop (deactivate) session for XMEGA targets
        """
        self.logger.debug("XMEGA-specific de-initialiser")
        self.avr.leave_progmode()
        self.avr.deactivate_physical()

    def read_device_id(self):
        """
        Read the device info

        :returns: Device ID raw bytes (little endian)
        """
        sig = self.avr.memory_read(self.avr.memtype_read_from_string("raw"), 0x01000090, 3)
        device_id_read = binary.unpack_be24(sig)
        self.logger.info("Device ID: '%06X'", device_id_read)
        # Return the raw signature bytes, but swap the endianness as target sends ID as Big endian
        return bytearray([sig[2], sig[1], sig[0]])

    def erase(self, memory_info=None, address=None):
        """
        Do a chip erase of the device
        """
        _dummy = memory_info
        _dummy = address
        raise NotImplementedError("NVM erase is not supported for XMEGA stack")

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
        raise NotImplementedError("NVM write is not supported for XMEGA stack")

    @staticmethod
    def read(memory_info, offset, numbytes):
        """
        Read the memory in chunks

        :param memory_info: dictionary for the memory as provided by the DeviceMemoryInfo class
        :param offset: relative offset in the memory type
        :param numbytes: number of bytes to read
        :return: array of bytes read
        """
        _dummy = memory_info
        _dummy = offset
        _dummy = numbytes
        raise NotImplementedError("NVM read is not supported for XMEGA stack")
