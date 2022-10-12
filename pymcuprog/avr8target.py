"""
Device Specific Classes which use AVR8Protocol implementation
"""
import time
from logging import getLogger
from pyedbglib.protocols.avr8protocol import Avr8Protocol
from pyedbglib.protocols.jtagice3protocol import Jtagice3ResponseError
from pyedbglib.util import binary

from .deviceinfo import deviceinfo
from .deviceinfo.memorynames import MemoryNames
from .deviceinfo.deviceinfokeys import DeviceInfoKeys, DeviceInfoKeysAvr, DeviceMemoryInfoKeys
from .pymcuprog_errors import PymcuprogError

class AvrDevice(object):
    """
    Generic AVR device wrapper (maps to avr8 protocol)
    """
    def __init__(self, transport):
        self.logger = getLogger(__name__)
        self.skip_blank_pages = True
        self.protocol = Avr8Protocol(transport)
        # AVR8 protocol packet framer limit
        self.max_read_chunk_size = 512
        self.max_write_chunk_size = 512

    @staticmethod
    def memtype_read_from_string(memtype_string):
        """
        Maps from a string to an avr8 memtype for reads

        :param memtype_string: Friendly name of memory
        :type memtype_string: str
        :returns: Memory type identifier as defined in the protocol
        :rtype: int
        """
        if memtype_string == MemoryNames.FLASH:
            memtype = Avr8Protocol.AVR8_MEMTYPE_FLASH_PAGE
        elif memtype_string == MemoryNames.EEPROM:
            memtype = Avr8Protocol.AVR8_MEMTYPE_EEPROM
        elif memtype_string in [MemoryNames.USER_ROW]:
            memtype = Avr8Protocol.AVR8_MEMTYPE_USER_SIGNATURE
        elif memtype_string in [MemoryNames.SIGNATURES]:
            memtype = Avr8Protocol.AVR8_MEMTYPE_CALIBRATION_SIGNATURE
        elif memtype_string == MemoryNames.FUSES:
            memtype = Avr8Protocol.AVR8_MEMTYPE_FUSES
        elif memtype_string in ("lock", MemoryNames.LOCKBITS):
            memtype = Avr8Protocol.AVR8_MEMTYPE_LOCKBITS
        elif memtype_string in ("raw", MemoryNames.INTERNAL_SRAM):
            memtype = Avr8Protocol.AVR8_MEMTYPE_SRAM
        else:
            memtype = 0
        return memtype

    def enter_progmode(self):
        """
        Enter programming mode
        """
        return self.protocol.enter_progmode()

    def leave_progmode(self):
        """
        Leave programming mode
        """
        return self.protocol.leave_progmode()

    def activate_physical(self):
        """
        Activate the physical interface
        """
        return self.protocol.activate_physical()

    def deactivate_physical(self):
        """
        Deactivate the physical interface
        """
        return self.protocol.deactivate_physical()

    def erase(self, mode=0, address=0):
        """
        Erase NVM

        :param mode: Flash erase mode to use
        :type mode: int
        :param address: Start address to erase from (not used by some modes)
        :type address: int
        """
        return self.protocol.erase(mode, address)

    def memory_read(self, memory_name, start_address, numbytes):
        """
        Read device memory

        :param memory_name: Memory type identifier as defined in the protocol
        :type memory_name: int
        :param start_address: First address to read
        :type start_address: int
        :param numbytes: Number of bytes to read
        :type numbytes: int
        :returns: Data read out
        :rtype: bytearray
        """
        return self.protocol.memory_read(memory_name, start_address, numbytes)

    def memory_write(self, memory_name, start_address, data):
        """
        Write device memory

        :param memory_name: Memory type identifier as defined in the protocol
        :type memory_name: int
        :param start_address: First address to write
        :type start_address: int
        :param data: Data to write
        :type data: bytearray
        """
        return self.protocol.memory_write(memory_name, start_address, data)

    @staticmethod
    def is_blank(data):
        """
        Checks if a buffer represents "blank" flash

        :param data: Contents to check
        :type data: bytearray
        :returns: True if data represents blank flash
        :rtype: boolean
        """
        for dat in data:
            if not dat == 0xFF:
                return False
        return True

    def read_memory_section(self, memory_type, start_address, bytes_to_read, read_chunk_size):
        """
        Reads a chunked section of memory

        :param memory_type: Memory type identifier as defined in the protocol
        :type memory_type: int
        :param start_address: First address to read
        :type start_address: int
        :param bytes_to_read: Number of bytes to read
        :type bytes_to_read: int
        :param read_chunk_size: Number of bytes in each separate read command to the debugger
        :type read_chunk_size: int
        """
        # AVR8 protocol packet framer limit
        if read_chunk_size > self.max_read_chunk_size:
            read_chunk_size = self.max_read_chunk_size
        # Check alignment
        if bytes_to_read != read_chunk_size and start_address % read_chunk_size != 0:
            raise PymcuprogError("Misaligned read")
        data = bytearray()
        while bytes_to_read:
            if bytes_to_read < read_chunk_size:
                read_chunk_size = bytes_to_read
            self.logger.info("Reading from address 0x%06X", start_address)
            data.extend(self.protocol.memory_read(memory_type, start_address, read_chunk_size))
            start_address += read_chunk_size
            bytes_to_read -= read_chunk_size
        return data

    def write_memory_section(self, memory_type, start_address, data_to_write, write_chunk_size, allow_blank_skip=False):
        """
        Writes a chunked section of memory

        :param memory_type: Memory type identifier as defined in the protocol
        :type memory_type: int
        :param start_address: First address to write to
        :type start_address: int
        :param data_to_write: Raw data values to write
        :type data_to_write: bytearray
        :param write_chunk_size: Number of bytes in each separate write command to the debugger
        :type write_chunk_size: int
        :param allow_blank_skip: Allow skipping write of locations with value 0xFF
        :type allow_blank_skip: boolean
        """
        # AVR8 protocol packet framer limit
        if write_chunk_size > self.max_write_chunk_size:
            write_chunk_size = self.max_write_chunk_size

        total_bytes_to_write = len(data_to_write)
        if write_chunk_size > total_bytes_to_write:
            write_chunk_size = total_bytes_to_write

        while data_to_write:
            chunk = data_to_write[0:write_chunk_size]
            if not self.skip_blank_pages or not self.is_blank(chunk) or not allow_blank_skip:
                self.protocol.memory_write(memory_type, start_address, chunk)
            start_address += write_chunk_size
            data_to_write = data_to_write[write_chunk_size:]


class TinyXAvrTarget(AvrDevice):
    """
    Class handling sessions with TinyX AVR targets using the AVR8 generic protocol
    """

    def __init__(self, transport):
        super(TinyXAvrTarget, self).__init__(transport)
        self.logger = getLogger(__name__)
        self.use_hv = Avr8Protocol.UPDI_HV_NONE

        if transport.device.product_string.lower().startswith('edbg'):
            # This is a workaround for FW3G-158 which has not been fixed for EDBG (fixed in common,
            # but no new EDBG firmware has/will be built)
            self.max_read_chunk_size = 256

    @staticmethod
    def memtype_write_from_string(memtype_string):
        """
        Maps from a string to an avr8 memtype for writes

        :param memtype_string: Friendly name of memory
        :type memtype_string: str
        :returns: Memory type identifier as defined in the protocol
        :rtype: int
        """
        if memtype_string == MemoryNames.EEPROM:
            # For UPDI devices erase is not implicit for the normal eeprom memory type so the special
            # atomic eeprom memory type must be used to avoid having to do an erase upfront
            memtype = Avr8Protocol.AVR8_MEMTYPE_EEPROM_ATOMIC
        else:
            # For most memories the same memory types are used for both read and write
            memtype = AvrDevice.memtype_read_from_string(memtype_string)
        return memtype

    def setup_prog_session(self,
                           interface=Avr8Protocol.AVR8_PHY_INTF_PDI_1W,
                           khz=900,
                           use_hv=Avr8Protocol.UPDI_HV_NONE):
        """
        Sets up a programming session for a tinyX AVR device

        :param interface: Physical interface to use
        :type interface: int
        :param khz: Clock speed in kiloHertz / baud in kbps
        :type khz: int
        :param use_hv: Use high-voltage pulse to activate UPDI
        :type use_hv: int
        """
        # TinyX variant
        self.protocol.set_variant(Avr8Protocol.AVR8_VARIANT_TINYX)
        # Prog functionality
        self.protocol.set_function(Avr8Protocol.AVR8_FUNC_PROGRAMMING)
        # Interface
        self.protocol.set_interface(interface)
        # UPDI uses XMEGA PDI clock
        self.protocol.set_le16(Avr8Protocol.AVR8_CTXT_PHYSICAL, Avr8Protocol.AVR8_PHY_XM_PDI_CLK, khz)
        # Set high-voltage activation
        # Note that this flag is always set even when use_hv is UPDI_HV_NONE to make it possible to disable high-voltage
        # activation again after it has previously been enabled.  The side effect is that this parameter might be
        # written to tools without high-voltage capability in which case this option parameter is not implemented.
        # However the protocol implementation will just consume the parameter value and ignore it.
        self.protocol.set_byte(Avr8Protocol.AVR8_CTXT_OPTIONS, Avr8Protocol.AVR8_OPT_HV_UPDI_ENABLE, use_hv)
        self.use_hv = use_hv

    def sib_read(self):
        """
        Reads the System Information Block

        :return: SIB bytes
        """
        return self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_SIB, 0, 32)

    def setup_config(self, device_info):
        """
        Sets up the device config for a tinyX AVR device

        :param device_info: Target device information as returned by deviceinfo.deviceinfo.getdeviceinfo
        :type device_info: dict
        """
        if device_info is None:
            device_info = {}

        # Parse the device info for memory descriptions
        device_memory_info = deviceinfo.DeviceMemoryInfo(device_info)

        flash_info = device_memory_info.memory_info_by_name(MemoryNames.FLASH)
        eeprom_info = device_memory_info.memory_info_by_name(MemoryNames.EEPROM)
        # Extract settings
        fl_base = flash_info[DeviceMemoryInfoKeys.ADDRESS]
        fl_page_size = flash_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        fl_size = flash_info[DeviceMemoryInfoKeys.SIZE]
        ee_base = eeprom_info[DeviceMemoryInfoKeys.ADDRESS]
        ee_page_size = eeprom_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        ee_size = eeprom_info[DeviceMemoryInfoKeys.SIZE]
        nvmctrl_addr = device_info.get(DeviceInfoKeysAvr.NVMCTRL_BASE)
        ocd_addr = device_info.get(DeviceInfoKeysAvr.OCD_BASE)
        user_row_base = device_memory_info.memory_info_by_name(MemoryNames.USER_ROW)[DeviceMemoryInfoKeys.ADDRESS]
        user_row_size = device_memory_info.memory_info_by_name(MemoryNames.USER_ROW)[DeviceMemoryInfoKeys.SIZE]
        sig_row_base = device_memory_info.memory_info_by_name(MemoryNames.SIGNATURES)[DeviceMemoryInfoKeys.ADDRESS]
        fuses_base = device_memory_info.memory_info_by_name(MemoryNames.FUSES)[DeviceMemoryInfoKeys.ADDRESS]
        fuse_size = device_memory_info.memory_info_by_name(MemoryNames.FUSES)[DeviceMemoryInfoKeys.SIZE]
        lock_base = device_memory_info.memory_info_by_name(MemoryNames.LOCKBITS)[DeviceMemoryInfoKeys.ADDRESS]
        device_id = device_info.get(DeviceInfoKeys.DEVICE_ID)
        hv_implementation = device_info.get(DeviceInfoKeysAvr.HV_IMPLEMENTATION)

        # Setup device structure and write to tool
        # TINYX_PROG_BASE
        devdata = bytearray([fl_base & 0xff, (fl_base >> 8) & 0xff])
        # TINYX_FLASH_PAGE_BYTES
        devdata += bytearray([fl_page_size & 0xff])
        # TINYX_EEPROM_PAGE_BYTES
        devdata += bytearray([ee_page_size])
        # TINYX_NVMCTRL_MODULE_ADDRESS
        devdata += bytearray([nvmctrl_addr & 0xff, (nvmctrl_addr >> 8) & 0xff])
        # TINYX_OCD_MODULE_ADDRESS
        devdata += bytearray([ocd_addr & 0xff, (ocd_addr >> 8) & 0xff])

        # Pad to get to TINYX_FLASH_BYTES
        devdata += bytearray([0x00]*(0x12-len(devdata)))

        # TINYX_FLASH_BYTES
        devdata += bytearray([fl_size & 0xFF, (fl_size >> 8) & 0xFF, (fl_size >> 16) & 0xFF, (fl_size >> 24) & 0xFF])
        # TINYX_EEPROM_BYTES
        devdata += bytearray([ee_size & 0xff, (ee_size >> 8) & 0xff])
        # TINYX_USER_SIG_BYTES_BYTES
        devdata += bytearray([user_row_size & 0xff, (user_row_size >> 8) & 0xff])
        # TINYX_FUSE_BYTES
        devdata += bytearray([fuse_size & 0xff])

        # Pad to get to TINYX_EEPROM_BASE
        devdata += bytearray([0x00]*(0x20-len(devdata)))

        # TINYX_EEPROM_BASE
        devdata += bytearray([ee_base & 0xFF, (ee_base >> 8) & 0xFF])
        # TINYX_USER_ROW_BASE
        devdata += bytearray([user_row_base & 0xFF, (user_row_base >> 8) & 0xFF])
        #TINYX_SIGROW_BASE
        devdata += bytearray([sig_row_base & 0xFF, (sig_row_base >> 8) & 0xFF])
        #TINYX_FUSES_BASE
        devdata += bytearray([fuses_base & 0xFF, (fuses_base >> 8) & 0xFF])
        # TINYX_LOCK_BASE
        devdata += bytearray([lock_base & 0xFF, (lock_base >> 8) & 0xFF])
        # TINYX_DEVICE_ID
        devdata += bytearray([device_id & 0xFF, (device_id >> 8) & 0xFF])
        # TINYX_PROG_BASE_MSB
        devdata += bytearray([(fl_base >> 16) & 0xFF])
        # TINYX_FLASH_PAGE_BYTES_MSB
        devdata += bytearray([(fl_page_size >> 8) & 0xFF])
        # TINYX_ADDRESS_SIZE
        if device_info.get(DeviceInfoKeysAvr.ADDRESS_SIZE, '16-bit') == '24-bit':
            # Use 24-bit addressing mode
            devdata += bytearray([0x01])
        else:
            # Default is 16-bit addressing mode
            devdata += bytearray([0x00])
        # TINYX_HV_IMPLEMENTATION
        devdata += bytearray([hv_implementation & 0xFF])

        self.protocol.write_device_data(devdata)

    def setup_debug_session(self,
                            interface=Avr8Protocol.AVR8_PHY_INTF_PDI_1W,
                            khz=100,
                            use_hv=Avr8Protocol.UPDI_HV_NONE):
        """
        Sets up a debug session for a tinyX AVR device

        :param interface: Physical interface to use
        :type interface: int
        :param khz: Clock speed in kiloHertz / baud in kbps
        :type khz: int
        :param use_hv: Use high-voltage pulse to activate UPDI
        :type use_hv: int
        """
        if interface == Avr8Protocol.AVR8_PHY_INTF_PDI_1W and use_hv != Avr8Protocol.UPDI_HV_NONE:
            self.protocol.set_byte(Avr8Protocol.AVR8_CTXT_OPTIONS, Avr8Protocol.AVR8_OPT_HV_UPDI_ENABLE, use_hv)
        self.protocol.set_variant(Avr8Protocol.AVR8_VARIANT_TINYX)
        self.protocol.set_function(Avr8Protocol.AVR8_FUNC_DEBUGGING)
        self.protocol.set_interface(interface)
        self.protocol.set_le16(Avr8Protocol.AVR8_CTXT_PHYSICAL, Avr8Protocol.AVR8_PHY_XM_PDI_CLK, khz)
        self.use_hv = use_hv

    def stack_pointer_read(self):
        """
        Reads the stack pointer

        :returns: Stack pointer
        :rtype: bytearray
        """
        return self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_OCD, 0x18, 0x02)

    def breakpoint_set(self, address):
        """
        Sets the hardware breakpoint

        :param address: Address to break at
        :type address: int
        """
        resp = self.protocol.jtagice3_command_response(
            bytearray([Avr8Protocol.CMD_AVR8_HW_BREAK_SET, Avr8Protocol.CMD_VERSION0, 1, 1]) +
            binary.pack_le32(address) +
            bytearray([3]))
        return self.protocol.check_response(resp)

    def breakpoint_clear(self):
        """
        Clears the hardware breakpoint
        """
        resp = self.protocol.jtagice3_command_response(
            bytearray([Avr8Protocol.CMD_AVR8_HW_BREAK_CLEAR, Avr8Protocol.CMD_VERSION0, 1]))
        return self.protocol.check_response(resp)

    def execute_patch(self, instructions, flags=0x00):
        """
        Executes an instruction in the AVR core

        :param instructions: Instructions to execute
        :type instructions: bytearray
        :param flags: Execution flags
        :type flags: int
        """
        packet = bytearray([0x70, Avr8Protocol.CMD_VERSION0, flags, len(instructions) / 2])
        packet = packet + instructions
        resp = self.protocol.jtagice3_command_response(packet)
        return self.protocol.check_response(resp)

    def run_with_power_nap(self):
        """
        Execute run with power-nap enabled.  This command is deprecated.
        """
        self.protocol.set_byte(Avr8Protocol.AVR8_CTXT_OPTIONS, Avr8Protocol.AVR8_OPT_POWER_NAP, 0x01)
        self.protocol.run()

    def activate_physical(self, use_reset=False, user_interaction_callback=None):
        """
        Override function for high-voltage activation for UPDI

        :param use_reset: Use external reset line during activation (only used for Mega JTAG interface)
        :type use_reset: boolean
        :param user_interaction_callback: Callback to be called when user interaction is required,
            for example when doing UPDI high-voltage activation with user target power toggle.
            This function could ask the user to toggle power and halt execution waiting for the user
            to respond (this is default behavior if the callback is None), or if the user is another
            script it could toggle power automatically and then return.
        :type user_interaction_callback: function
        """
        try:
            return self.protocol.activate_physical(use_reset)
        except Jtagice3ResponseError as error:
            if error.code == Avr8Protocol.AVR8_FAILURE_PLEASE_TOGGLE_POWER:
                if self.use_hv == Avr8Protocol.UPDI_HV_USER_POWER_TOGGLE:
                    if user_interaction_callback is None:
                       # Default behavior is to wait for the user to toggle power
                        input("Toggle power now")
                    else:
                        user_interaction_callback()
                    # During pounce, or at window timeout, firmware clears the "user power toggle" flag
                    # However MPLAB will always set this before each activate, so the parameter is set again here
                    # to most-accurately reflect front-end behaviour for test purposes
                    self.protocol.set_byte(Avr8Protocol.AVR8_CTXT_OPTIONS,
                                           Avr8Protocol.AVR8_OPT_HV_UPDI_ENABLE, self.use_hv)
                    return self.protocol.activate_physical(use_reset)
            raise

    def ocdregfile_read(self):
        """
        Read OCD registers

        :return: OCD register file
        :rtype: bytearray
        """
        data = None
        for register_index in range(32):
            data = self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_OCD, register_index, 1)
            self.logger.info("OCDREG%02X=0x%02X", register_index, data)
        return data

    def execute_instruction(self, instruction):
        """
        Execute an AVR instruction on the core

        :param instruction: Instruction to execute
        :type instruction: int
        """
        value = 0x04
        self.logger.info("Write 0x%02X to CTRLA", value)
        status = self.protocol.memory_write(Avr8Protocol.AVR8_MEMTYPE_OCD, 0x08, value)
        self.logger.info("%s", status)

        self.logger.info("Write 0x%04X to ALTINST", instruction)
        status = self.protocol.memory_write(Avr8Protocol.AVR8_MEMTYPE_OCD, 0x10, instruction)
        self.logger.info("%s", status)

        # Write CS addr 4 (OCD RESTART)
        self.logger.info("OCD RESTART")
        status = self.protocol.memory_write(Avr8Protocol.AVR8_MEMTYPE_CS, 0x04, (1 << 1))
        self.logger.info("%s", status)
        while True:
            status = self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_CS, 0x05, 0x01)
            self.logger.info("waiting for stopped...(0x%02X)", status)
            if status:
                break
            time.sleep(0.001)

    def read_device_id(self):
        """
        Reads the device ID from the part

        :returns: Device ID raw bytes (little endian)
        :rtype: bytearray
        """
        self.logger.info("Read device ID")
        device_id = self.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_SRAM, 0x1100, 3)
        return device_id


class TinyAvrTarget(AvrDevice):
    """
    Implements Tiny AVR (debugWIRE) functionality of the AVR8 protocol
    """

    def __init__(self, transport):
        super(TinyAvrTarget, self).__init__(transport)
        self.logger = getLogger(__name__)

    def setup_debug_session(self):
        """
        Sets up a debugging session on an Tiny AVR (debugwire)
        """
        self.protocol.set_variant(Avr8Protocol.AVR8_VARIANT_TINYOCD)
        self.protocol.set_function(Avr8Protocol.AVR8_FUNC_DEBUGGING)
        self.protocol.set_interface(Avr8Protocol.AVR8_PHY_INTF_DW)

class MegaAvrJtagTarget(AvrDevice):
    """
    Implements Mega AVR (JTAG) functionality of the AVR8 protocol
    """

    def __init__(self, transport):
        super(MegaAvrJtagTarget, self).__init__(transport)
        self.logger = getLogger(__name__)

    def setup_prog_session(self):
        """
        Sets up a programming session on an Mega AVR (JTAG)
        """
        self.protocol.set_variant(Avr8Protocol.AVR8_VARIANT_MEGAOCD)
        self.protocol.set_function(Avr8Protocol.AVR8_FUNC_PROGRAMMING)
        self.protocol.set_interface(Avr8Protocol.AVR8_PHY_INTF_JTAG)

    def setup_config(self, device_info):
        """
        Sets up the device config for a mega AVR device

        :param device_info: Target device information as returned by deviceinfo.deviceinfo.getdeviceinfo
        :type device_info: dict
        """
        if device_info is None:
            device_info = {}

        # Parse the device info for memory descriptions
        device_memory_info = deviceinfo.DeviceMemoryInfo(device_info)

        flash_info = device_memory_info.memory_info_by_name(MemoryNames.FLASH)
        eeprom_info = device_memory_info.memory_info_by_name(MemoryNames.EEPROM)

        # Extract settings
        fl_base = flash_info[DeviceMemoryInfoKeys.ADDRESS]
        fl_page_size = flash_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        fl_size = flash_info[DeviceMemoryInfoKeys.SIZE]
        ee_page_size = eeprom_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        ee_size = eeprom_info[DeviceMemoryInfoKeys.SIZE]

        # Setup device structure and write to tool

        # TMEGA_FLASH_PAGE_BYTES              = 0x00,
        devdata = bytearray([fl_page_size & 0xff, (fl_page_size >> 8) & 0xff])

        # TMEGA_FLASH_BYTES                   = 0x02,
        devdata += bytearray([fl_size & 0xFF, (fl_size >> 8) & 0xFF, (fl_size >> 16) & 0xFF, (fl_size >> 24) & 0xFF])

        # TMEGA_FLASH_BASE                    = 0x06,
        devdata += bytearray([fl_base & 0xFF, (fl_base >> 8) & 0xFF, (fl_base >> 16) & 0xFF, (fl_base >> 24) & 0xFF])

        # TMEGA_SMALLEST_BOOT_START           = 0x0A,
        # Use last page for boot size (not correct, but sufficient for programming)
        boot_start = fl_size - fl_page_size
        devdata += bytearray([1+boot_start & 0xFF, (boot_start >> 8) & 0xFF, (boot_start >> 16) & 0xFF, (boot_start >> 24) & 0xFF])

        # TMEGA_SRAM_START                    = 0x0E,
        sram_start = 0x100
        devdata += bytearray([sram_start & 0xff, (sram_start >> 8) & 0xff])

        # TMEGA_EEPROM_BYTES                  = 0x10,
        devdata += bytearray([ee_size & 0xff, (ee_size >> 8) & 0xff])

        # TMEGA_EEPROM_PAGE_SIZE              = 0x12,
        devdata += bytearray([ee_page_size])

        # TMEGA_OCD_REV                       = 0x13,
        # OCD_REVISION in OCD property-group in ATDF
        devdata += bytearray([0x03])

        # TMEGA_PAGEBUFFERS_PER_FLASH_BLOCK   = 0x14,
        devdata += bytearray([0x01])

        # TMEGA_FULLPAGE_BITSTREAM            = 0x15,
        devdata += bytearray([0x00])

        # TMEGA_DEBUGWIRE_HARDWARE_BREAKPOINTS = 0x16,
        devdata += bytearray([0x00])

        # Free                               0x17,
        devdata += bytearray([0x00])

        # TINY/MEGA IO addresses
        # TMEGA_OCDREG_ADDR                   = 0x18,
        devdata += bytearray([0x51])

        # TMEGA_EEARH_ADDR                    = 0x19,
        devdata += bytearray([0x42])

        # TMEGA_EEARL_ADDR                    = 0x1A,
        devdata += bytearray([0x41])

        # TMEGA_EECR_ADDR                     = 0x1B,
        devdata += bytearray([0x3F])

        # TMEGA_EEDR_ADDR                     = 0x1C,
        devdata += bytearray([0x40])

        # TMEGA_SPMCR_ADDR                    = 0x1D,
        devdata += bytearray([0x57])

        # TMEGA_OSCCAL_ADDR                   = 0x1E
        devdata += bytearray([0x66])

        self.protocol.write_device_data(devdata)

class XmegaAvrTarget(AvrDevice):
    """
    Implements XMEGA (PDI) functionality of the AVR8 protocol
    """

    def __init__(self, transport):
        super(XmegaAvrTarget, self).__init__(transport)
        self.logger = getLogger(__name__)

        if transport.device.product_string.lower().startswith('edbg'):
            # This is a workaround for FW3G-158 which has not been fixed for EDBG (fixed in common,
            # but no new EDBG firmware has/will be built)
            self.max_read_chunk_size = 256

    def setup_debug_session(self):
        """
        Sets up a debugging session on an XMEGA AVR
        """
        self.protocol.set_variant(Avr8Protocol.AVR8_VARIANT_XMEGA)
        self.protocol.set_function(Avr8Protocol.AVR8_FUNC_DEBUGGING)
        self.protocol.set_interface(Avr8Protocol.AVR8_PHY_INTF_PDI)

    def setup_prog_session(self, interface=Avr8Protocol.AVR8_PHY_INTF_PDI, khz=4000):
        """
        Sets up a programming session for a XMEGA AVR device

        :param interface: physical interface to use
        :param khz: clock speed in kiloHertz
        """
        # XMEGA variant
        self.protocol.set_variant(Avr8Protocol.AVR8_VARIANT_XMEGA)
        # Prog functionality
        self.protocol.set_function(Avr8Protocol.AVR8_FUNC_PROGRAMMING)
        # Interface
        self.protocol.set_interface(interface)
        # PDI uses XMEGA PDI clock
        self.protocol.set_le16(Avr8Protocol.AVR8_CTXT_PHYSICAL, Avr8Protocol.AVR8_PHY_XM_PDI_CLK, khz)

    def setup_config(self, device_info):
        """
        Sets up the device config for a XMEGA AVR device

        :param device_info: target device information as returned by deviceinfo.deviceinfo.getdeviceinfo
        """
        if device_info is None:
            device_info = {}

        # Parse the device info for memory descriptions
        device_memory_info = deviceinfo.DeviceMemoryInfo(device_info)

        flash_info = device_memory_info.memory_info_by_name(MemoryNames.FLASH)
        eeprom_info = device_memory_info.memory_info_by_name(MemoryNames.EEPROM)

        # Extract settings
        fl_base = flash_info[DeviceMemoryInfoKeys.ADDRESS]
        fl_page_size = flash_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        fl_size = flash_info[DeviceMemoryInfoKeys.SIZE]
        ee_base = eeprom_info[DeviceMemoryInfoKeys.ADDRESS]
        ee_page_size = eeprom_info[DeviceMemoryInfoKeys.PAGE_SIZE]
        ee_size = eeprom_info[DeviceMemoryInfoKeys.SIZE]

        # Setup device structure and write to tool
        # XMEGA_APPL_BASE 0x00
        devdata = bytearray([fl_base & 0xff, (fl_base >> 8) & 0xff, (fl_base >> 16) & 0xff, (fl_base >> 24) & 0xff])

        # XMEGA_BOOT_BASE 0x04
        boot_base = 0x00820000
        devdata += bytearray([boot_base & 0xff, (boot_base >> 8) & 0xff, (boot_base >> 16) & 0xff, (boot_base >> 24) & 0xff])

        # XMEGA_EEPROM_BASE 0x08
        devdata += bytearray([ee_base & 0xff, (ee_base >> 8) & 0xff, (ee_base >> 16) & 0xff, (ee_base >> 24) & 0xff])

        # XMEGA_FUSE_BASE 0x0C
        fuses_base = 0x008F0020
        devdata += bytearray([fuses_base & 0xff, (fuses_base >> 8) & 0xff, (fuses_base >> 16) & 0xff, (fuses_base >> 24) & 0xff])

        # XMEGA_LOCKBIT_BASE 0x10
        lock_base = 0x008F0027
        devdata += bytearray([lock_base & 0xff, (lock_base >> 8) & 0xff, (lock_base >> 16) & 0xff, (lock_base >> 24) & 0xff])

        # XMEGA_USER_SIGN_BASE 0x14
        user_row_base = 0x008E0400
        devdata += bytearray([user_row_base & 0xff, (user_row_base >> 8) & 0xff, (user_row_base >> 16) & 0xff, (user_row_base >> 24) & 0xff])

        # XMEGA_PROD_SIGN_BASE 0x18
        sig_row_base = 0x008E0200
        devdata += bytearray([sig_row_base & 0xff, (sig_row_base >> 8) & 0xff, (sig_row_base >> 16) & 0xff, (sig_row_base >> 24) & 0xff])

        # XMEGA_DATA_BASE 0x1C
        data_space_base = 0x01000000
        devdata += bytearray([data_space_base & 0xff, (data_space_base >> 8) & 0xff, (data_space_base >> 16) & 0xff, (data_space_base >> 24) & 0xff])

        # XMEGA_APPL_BYTES 0x20
        devdata += bytearray([fl_size & 0xFF, (fl_size >> 8) & 0xFF, (fl_size >> 16) & 0xFF, (fl_size >> 24) & 0xFF])

        # XMEGA_BOOT_BYTES 0x24
        fl_boot_size = 512
        devdata += bytearray([fl_boot_size & 0xff, (fl_boot_size >> 8) & 0xff])

        # XMEGA_FLASH_PAGE_BYTES 0x26
        devdata += bytearray([fl_page_size & 0xff, (fl_page_size >> 8) & 0xff])

        # XMEGA_EEPROM_SIZE 0x28
        devdata += bytearray([ee_size & 0xff, (ee_size >> 8) & 0xff])

        # XMEGA_EEPROM_PAGE_SIZE 0x2A
        devdata += bytearray([ee_page_size])

        # XMEGA_NVM_OFFSET 0x2B
        nvm_offset = 0x01C0
        devdata += bytearray([nvm_offset & 0xff, (nvm_offset >> 8) & 0xff])

        # XMEGA_SIGN_OFFSET 0x2D
        signature_offset = 0x0090
        devdata += bytearray([signature_offset & 0xff, (signature_offset >> 8) & 0xff])

        # Write to the debugger
        self.protocol.write_device_data(devdata)
