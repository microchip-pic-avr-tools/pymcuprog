"""
pyupdi-esque NVM implementation
"""
import binascii

from pyedbglib.util import binary

from . import utils
from .nvm import NvmAccessProvider
from .deviceinfo import deviceinfo
from .deviceinfo.deviceinfokeys import DeviceInfoKeysAvr, DeviceMemoryInfoKeys
from .deviceinfo.memorynames import MemoryNames
from .serialupdi.application import UpdiApplication
from .pymcuprog_errors import PymcuprogSessionError, PymcuprogDeviceLockedError, PymcuprogSerialUpdiLockedError

# This is a data class so it should not need any methods but will have many instance variables
# pylint: disable=too-many-instance-attributes,too-few-public-methods
class Dut:
    """
    Create a device object for UpdiApplication
    """

    def __init__(self, dev_info):
        # Parse the device info for memory descriptions
        device_memory_info = deviceinfo.DeviceMemoryInfo(dev_info)

        flash_info = device_memory_info.memory_info_by_name(MemoryNames.FLASH)
        self.flash_start = flash_info[DeviceMemoryInfoKeys.ADDRESS]
        self.flash_size = flash_info[DeviceMemoryInfoKeys.SIZE]
        self.flash_pagesize = flash_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        self.syscfg_address = dev_info[DeviceInfoKeysAvr.SYSCFG_BASE]
        self.nvmctrl_address = dev_info[DeviceInfoKeysAvr.NVMCTRL_BASE]
        address_key = DeviceMemoryInfoKeys.ADDRESS
        self.sigrow_address = device_memory_info.memory_info_by_name(MemoryNames.SIGNATURES)[address_key]
        self.fuses_address = device_memory_info.memory_info_by_name(MemoryNames.FUSES)[address_key]
        self.userrow_address = device_memory_info.memory_info_by_name(MemoryNames.USER_ROW)[address_key]


class NvmAccessProviderSerial(NvmAccessProvider):
    """
    NVM Access the Python AVR way
    """

    def __init__(self, transport, device_info, options=""):
        """
        NVM Access provider for serialUPDI

        :param transport: transport object describing serial port connection
        :type transport: ToolSerialConnection object
        :param device_info: dictionary describing the target device
        :type device_info: dict
        :param options: additional options to use in this session
        :type options: str
        """
        port = transport.serialport
        timeout = transport.timeout
        baudrate = transport.baudrate
        self.avr = None
        self.options = options
        NvmAccessProvider.__init__(self, device_info)
        self.dut = Dut(device_info)
        self.avr = UpdiApplication(port, baudrate, self.dut, timeout=timeout)
        # Read the device info to set up the UPDI stack variant
        self.avr.read_device_info()

    def start(self, user_interaction_callback=None):
        """
        Start (activate) session for UPDI serial targets
        """
        try:
            self.avr.enter_progmode()
        except PymcuprogSerialUpdiLockedError:
            if ('user-row-locked-device' in self.options and self.options['user-row-locked-device']):
                self.logger.info("Device is locked. Proceeding to write USER ROW...")
            elif 'chip-erase-locked-device' in self.options and self.options['chip-erase-locked-device']:
                self.logger.info("Device is locked. Proceeding to chip erase to unlock...")
                self.avr.unlock()
            else:
                raise PymcuprogDeviceLockedError("Unable to enter programming mode: device is locked!")

    def read_device_id(self):
        """
        Read and display (log) the device info

        :returns: Device ID raw bytes (little endian)
        :raises PymcuprogSessionError: if device ID does not match
        """
        sib_info = self.avr.read_device_info()
        self.logger.info("Device family: '%s'", sib_info['family'])

        signatures_base = self.dut.sigrow_address

        # Read 3 bytes
        sig = self.avr.read_data(signatures_base, 3)
        if len(sig) != 3:
            self.logger.error("Unable to read signature for detected device in family: '%s'", sib_info['family'])
            raise PymcuprogSessionError("Unable to read device ID")

        device_id_read = binary.unpack_be24(sig)
        self.logger.info("Device ID: '%06X'", device_id_read)
        if not self.device_info.get(DeviceInfoKeysAvr.DEVICE_ID) == device_id_read:
            raise PymcuprogSessionError("Device ID mismatch: read out '{0:X}'; expected '{1:X}'.".format(device_id_read,
                                        self.device_info.get(DeviceInfoKeysAvr.DEVICE_ID)))
        revision = self.avr.read_data(self.device_info.get(DeviceInfoKeysAvr.SYSCFG_BASE) + 1, 1)

        self.logger.debug("Device revision: 0x%02x", revision[0])
        self.logger.info("Device revision: '%x.%x'", revision[0] >> 4, revision[0] & 0x0F)

        serial = self.avr.read_data(signatures_base + 3, 10)
        self.logger.info("Device serial number: '%s'", binascii.hexlify(serial))

        # Return the raw signature bytes, but swap the endianness as target sends ID as Big endian
        return bytearray([sig[2], sig[1], sig[0]])

    def erase(self, memory_info=None, address=None):
        """
        Do a chip erase of the device
        """
        if address is None:
            address = 0

        if memory_info is None:
            try:
                self.avr.nvm.chip_erase()
            except IOError as inst:
                self.logger.error("Device is locked. Performing unlock with chip erase.\nError: ('%s')", inst)
                self.avr.unlock()
        else:
            # Add the memory offset
            address += memory_info[DeviceMemoryInfoKeys.ADDRESS]
            memory_name = memory_info[DeviceMemoryInfoKeys.NAME]
            if memory_name == MemoryNames.EEPROM:
                self.avr.nvm.erase_eeprom()
            elif memory_name == MemoryNames.USER_ROW:
                self.avr.nvm.erase_user_row(address, memory_info[DeviceMemoryInfoKeys.SIZE])
            elif memory_name == MemoryNames.FLASH:
                # There is no single command for flash erase on UPDI parts so each page must be erased individually
                page_size = memory_info[DeviceMemoryInfoKeys.PAGE_SIZE]
                n_pages = memory_info[DeviceMemoryInfoKeys.SIZE]//page_size
                self.logger.debug("Erasing %d pages of flash", n_pages)
                for i in range(n_pages):
                    self.avr.nvm.erase_flash_page(address=address+i*page_size)
            else:
                try:
                    self.avr.nvm.chip_erase()
                except IOError as inst:
                    self.logger.error("Device is locked. Performing unlock with chip erase.\nError: ('%s')", inst)
                    self.avr.unlock()

    def write(self, memory_info, offset, data):
        """
        Write the memory with data

        :param memory_info: dictionary for the memory as provided by the DeviceMemoryInfo class
        :param offset: relative offset within the memory type
        :param data: the data to program
        """
        # Make sure the data is aligned to a memory page
        data_aligned, offset_aligned = utils.pagealign(data,
                                                       offset,
                                                       memory_info[DeviceMemoryInfoKeys.PAGE_SIZE],
                                                       memory_info[DeviceMemoryInfoKeys.WRITE_SIZE])
        memtype_string = memory_info[DeviceMemoryInfoKeys.NAME]

        offset_aligned += memory_info[DeviceMemoryInfoKeys.ADDRESS]

        # Is this a write to user row on a locked device?
        user_row_write_locked_device = (memtype_string == MemoryNames.USER_ROW) and \
            ('user-row-locked-device' in self.options and self.options['user-row-locked-device'])

        if memtype_string in (MemoryNames.FLASH, MemoryNames.EEPROM, MemoryNames.FUSES, MemoryNames.LOCKBITS) or user_row_write_locked_device:
            write_chunk_size = memory_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        else:
            write_chunk_size = len(data_aligned)

        if user_row_write_locked_device:
            self.logger.info("Padding user row to %d bytes", memory_info[DeviceMemoryInfoKeys.PAGE_SIZE])
            data_aligned = utils.pad_to_size(data_aligned, memory_info[DeviceMemoryInfoKeys.PAGE_SIZE], 0xFF)
            self.logger.info("Writing USER ROW on locked device...")
            self.avr.write_user_row_locked_device(offset_aligned, data_aligned)
            return

        while data_aligned:
            if len(data_aligned) < write_chunk_size:
                write_chunk_size = len(data_aligned)
            chunk = data_aligned[0:write_chunk_size]
            self.logger.debug("Writing %d bytes to address 0x%06X", write_chunk_size, offset_aligned)
            if memtype_string == MemoryNames.FUSES:
                self.avr.nvm.write_fuse(offset_aligned, chunk)
            elif memtype_string == MemoryNames.LOCKBITS:
                # Lockbits are accessed like fuses
                self.avr.nvm.write_fuse(offset_aligned, chunk)
            elif memtype_string == MemoryNames.EEPROM:
                self.avr.nvm.write_eeprom(offset_aligned, chunk)
            elif memtype_string == MemoryNames.USER_ROW:
                self.avr.nvm.write_user_row(offset_aligned, chunk)
            elif memtype_string == MemoryNames.BOOT_ROW:
                self.avr.nvm.write_user_row(offset_aligned, chunk)
            else:
                self.avr.nvm.write_flash(offset_aligned, chunk)
            offset_aligned += write_chunk_size
            data_aligned = data_aligned[write_chunk_size:]

    def read(self, memory_info, offset, numbytes):
        """
        Read the memory in chunks

        :param memory_info: dictionary for the memory as provided by the DeviceMemoryInfo class
        :param offset: relative offset in the memory type
        :param numbytes: number of bytes to read
        :return: array of bytes read
        """
        offset += memory_info[DeviceMemoryInfoKeys.ADDRESS]

        data = bytearray()
        read_chunk_size = 0x100
        while numbytes:
            if numbytes < read_chunk_size:
                read_chunk_size = numbytes
            self.logger.debug("Reading %d bytes from address 0x%06X", read_chunk_size, offset)
            data += self.avr.read_data(offset, read_chunk_size)
            offset += read_chunk_size
            numbytes -= read_chunk_size

        return data

    def hold_in_reset(self):
        """
        Hold device in reset
        """
        # For UPDI parts it is sufficient to enter programming mode to hold the target in reset
        # Since the start function is a prerequisite to all functions in this file it can be
        # assumed that programming mode already has been entered
        return

    def release_from_reset(self):
        """
        Release device from reset
        """
        # Entering programming mode on UPDI parts will hold the device in reset.  So to release
        # the reset the programming mode must be left.
        self.avr.leave_progmode()

    def stop(self):
        """
        Stop the debugging session
        """
        if self.avr is not None:
            self.avr.leave_progmode()
