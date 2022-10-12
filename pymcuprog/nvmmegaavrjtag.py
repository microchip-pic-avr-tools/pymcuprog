"""
AVR mega JTAG NVM implementation
NB: This is a stub - not all features are implemented
"""
from pyedbglib.protocols.jtagice3protocol import Jtagice3ResponseError
from pyedbglib.protocols.avr8protocol import Avr8Protocol

from .nvm import NvmAccessProviderCmsisDapAvr
from .avr8target import MegaAvrJtagTarget
from .pymcuprog_errors import PymcuprogError, PymcuprogSessionError

from .deviceinfo.deviceinfokeys import DeviceInfoKeysAvr, DeviceMemoryInfoKeys
from .deviceinfo.memorynames import MemoryNames

class NvmAccessProviderCmsisDapMegaAvrJtag(NvmAccessProviderCmsisDapAvr):
    """
    NVM Access the megaJTAG way
    """

    def __init__(self, transport, device_info):
        NvmAccessProviderCmsisDapAvr.__init__(self, device_info)

        self._log_incomplete_stack('megaAVR-JTAG')
        self.avr = MegaAvrJtagTarget(transport)
        self.avr.setup_config(device_info)
        self.avr.setup_prog_session()

    def __del__(self):
        pass

    def start(self, user_interaction_callback=None):
        """
        Start (activate) session for megaJTAG targets
        """
        try:
            resp = self.avr.activate_physical()
        except Jtagice3ResponseError as error:
            # The debugger could be out of sync with the target, retry
            if error.code == Avr8Protocol.AVR8_FAILURE_INVALID_PHYSICAL_STATE:
                self.logger.info("Physical state out of sync.  Retrying.")
                self.avr.deactivate_physical()
                self.avr.activate_physical()
            else:
                raise PymcuprogSessionError("Unable to activate JTAG interface.  Maybe its disabled?")

        self.logger.info("JTAG ID read: %02X%02X%02X%02X", resp[3], resp[2], resp[1], resp[0])
        if resp[0] != 0x3F:
            raise PymcuprogSessionError("Non-Atmel/Microchip JTAG device detected!")
        self.avr.enter_progmode()

    def stop(self):
        """
        Stop (deactivate) session for megaJTAG targets
        """
        self.avr.leave_progmode()
        self.avr.deactivate_physical()

    def read_device_id(self):
        """
        Read the device info

        :returns: Device ID raw bytes (little endian)
        """
        resp = self.avr.memory_read(Avr8Protocol.AVR8_MEMTYPE_SIGNATURE, 0, 3)
        self.logger.info("Device signature read: %02X%02X%02X", resp[0], resp[1], resp[2])
        return bytearray([resp[2], resp[1], resp[0]])

    def erase(self, memory_info=None, address=None):
        """
        Do a chip erase of the device
        """
        _dummy = memory_info
        _dummy = address
        self.logger.info("Only full CHIP ERASE is available on mega JTAG")
        self.avr.erase(Avr8Protocol.ERASE_CHIP, 0)

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
        raise NotImplementedError("NVM write is not supported for megaJTAG stack")

    def read(self, memory_info, offset, numbytes):
        """
        Read the memory in chunks

        :param memory_info: dictionary for the memory as provided by the DeviceMemoryInfo class
        :param offset: relative offset in the memory type
        :param numbytes: number of bytes to read
        :return: array of bytes read
        """
        memtype_string = memory_info[DeviceMemoryInfoKeys.NAME]
        memtype = self.avr.memtype_read_from_string(memtype_string)
        if memtype == 0:
            msg = "Unsupported memory type: {}".format(memtype_string)
            self.logger.error(msg)
            raise PymcuprogError(msg)

        if not memtype_string == MemoryNames.FLASH:
            # Flash is offset by the debugger config
            try:
                offset += memory_info[DeviceMemoryInfoKeys.ADDRESS]
            except TypeError:
                pass

        # EEPROM is only accessible as paged EEPROM on megaJTAG interface
        if memtype == Avr8Protocol.AVR8_MEMTYPE_EEPROM:
            memtype = Avr8Protocol.AVR8_MEMTYPE_EEPROM_PAGE

        data = self.avr.read_memory_section(memtype, offset, numbytes, numbytes)
        return data
