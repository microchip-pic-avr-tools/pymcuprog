"""
Python AVR MCU debugger
"""
import time
from logging import getLogger
from pyedbglib.protocols import housekeepingprotocol
from pyedbglib.protocols.avr8protocol import Avr8Protocol
from pyedbglib.util import binary

from .deviceinfo import deviceinfo
from .nvmupdi import NvmAccessProviderCmsisDapUpdi
from .pymcuprog_errors import PymcuprogToolConfigurationError, PymcuprogNotSupportedError, PymcuprogError

class AvrDebugger():
    """
    AVR debugger wrapper

    :param transport: transport object to communicate through
    :type transport: object(hid_transport)
    :param use_events_for_run_stop_state: True to use HID event channel, False to polling
    :type use_events_for_run_stop_state: boolean
    """
    def __init__(self, transport, use_events_for_run_stop_state=True):
        # Hook onto logger
        self.logger = getLogger(__name__)
        # Use transport passed in
        self.transport = transport
        self.device_info = None
        self.memory_info = None
        self.device_info = None
        self.device = None

        # Event polling needs a housekeeping session to subscribe to run/stop events
        self.housekeeper = None
        self.use_events_for_run_stop_state = use_events_for_run_stop_state
        if self.use_events_for_run_stop_state:
            self.housekeeper = housekeepingprotocol.Jtagice3HousekeepingProtocol(self.transport)
            self.housekeeper.start_session()

    def setup_session(self, device, frequency=900000, options=""):
        """
        Sets up the device for a debug session

        :param device: name of the device to debug
        :param frequency: UPDI clock frequency in Hz
        :type frequency: int
        :param options: dictionary of options for starting the session
        :type options: dict
        """
        self.logger.info("Setting up %s for debugging", device)

        # Gather device info
        try:
            self.device_info = deviceinfo.getdeviceinfo(device)
        except ImportError:
            raise PymcuprogNotSupportedError("No device info for device: {}".format(device))
        if self.device_info['interface'].upper() != "UPDI":
            raise PymcuprogToolConfigurationError("pymcuprog debug wrapper only supports UPDI devices")

        # Memory info for the device
        self.memory_info = deviceinfo.DeviceMemoryInfo(self.device_info)

        # Setup device model and start a session
        self.device = NvmAccessProviderCmsisDapUpdi(self.transport, self.device_info, frequency, options)

        # Default setup for NVM Access Provider is prog session - override with debug info
        self.device.avr.setup_debug_session(interface=Avr8Protocol.AVR8_PHY_INTF_PDI_1W,
                                            khz=frequency // 1000,
                                            use_hv=Avr8Protocol.UPDI_HV_NONE)

    def start_debugging(self, flash_data=None):
        """
        Start the debug session

        :param flash_data: flash data content to program in before debugging
        :type flash data: list of bytes
        """
        self.logger.info("Starting debug session")
        self.device.start()

        # The device is now in prog mode
        device_id = self.device.read_device_id()
        self.logger.debug("Device ID read: %X", binary.unpack_le24(device_id))

        # If the user wants content on the AVR, put it there now
        if flash_data:
            if not isinstance(flash_data, list):
                raise PymcuprogNotSupportedError("Content can only be provided as a list of binary values")
            # First chip-erase
            self.logger.info("Erasing target")
            self.device.erase()

            # Then program
            self.logger.info("Programming target")
            self.device.write(self.memory_info.memory_info_by_name('flash'), 0, flash_data)

        # Flush events before starting
        self.flush_events()

        self.logger.info("Leaving prog mode (with auto-attach)")
        self.device.avr.protocol.leave_progmode()

        self._wait_for_break()

    # Cleanup code for detatching target
    def stop_debugging(self):
        """
        Stop the debug session and clean up
        """
        self.logger.info("Stop debugging session")
        # Halt the core
        self.device.avr.protocol.stop()
        # Remove all software breakpoints
        self.device.avr.protocol.software_breakpoint_clear_all()
        # Remove all hardware  breakpoints
        self.device.avr.breakpoint_clear()
        # Detach from the OCD
        self.device.avr.protocol.detach()
        # De-activate UPDI physical interface
        self.device.avr.deactivate_physical()
        # Sign off
        if self.use_events_for_run_stop_state:
            self.housekeeper.end_session()

    def __exit__(self, exc_type, exc_value, traceback):
        """ Destructor"""
        self.stop_debugging()

    def _read_running_state(self):
        """
        Back-channel interface to see what state the AVR is in
        This mechanism can be used to replace relying on AVR_EVT events which publish stop conditions
        """
        running = self.device.avr.protocol.get_byte(Avr8Protocol.AVR8_CTXT_TEST, Avr8Protocol.AVR8_TEST_TGT_RUNNING)
        if running:
            self.logger.debug("AVR core is running")
        else:
            self.logger.debug("AVR core is stopped")
        return bool(running)

    def _wait_for_break(self, timeout_ms=1000):
        """
        Wait for the AVR core to be in stopped/halt/break state

        :param timeout_ms: number of milliseconds to wait
        :type timeout_ms: int
        """
        if self.use_events_for_run_stop_state:
            while True:
                program_counter = self.poll_event()
                if program_counter is not None:
                    return
                timeout_ms -= 50
                time.sleep(0.05)
                if timeout_ms < 0:
                    raise PymcuprogError("Timeout waiting for AVR core to halt")
        else:
            while True:
                if not self._read_running_state():
                    return
                timeout_ms -= 50
                time.sleep(0.05)
                if timeout_ms < 0:
                    raise PymcuprogError("Timeout waiting for AVR core to halt")

    # Debugging functions, using protocol object in device model directly
    def attach(self, do_break=False):
        """
        Attach to the AVR core

        :param do_break: set to True to force the core to stop during attach
        :type do_break: bool
        """
        self.logger.debug("Attach debugger to AVR core")
        self.device.avr.protocol.attach(do_break)
        if do_break:
            self._wait_for_break()

    def detach(self):
        """
        Detach from the AVR core
        """
        self.logger.debug("Detach from AVR core")
        self.device.avr.protocol.detach()

    # Flow control
    def reset(self):
        """
        Reset the AVR core.
        The PC will point to the first instruction to be executed.
        """
        self.logger.debug("CPU reset")
        self.device.avr.protocol.reset()
        self._wait_for_break()

    def step(self):
        """
        Single-step on protocol level
        Executes a single AVR instruction, regardless of number of cycles
        """
        self.logger.debug("CPU single-instruction-step")
        self.device.avr.protocol.step()
        self._wait_for_break()

    def stop(self):
        """
        Request the AVR core to halt and wait for it to enter stopped state
        """
        self.logger.debug("CPU halt")
        self.device.avr.protocol.stop()
        self._wait_for_break()

    def run(self):
        """
        Put the AVR core into run mode
        """
        self.logger.debug("CPU resume")
        self.device.avr.protocol.run()

    def run_to(self, address):
        """
        Insert a breakpoint at the given address and put the core into run mode
        Does not wait for the address to be reached

        :param address: byte address of the instruction to break at
        """
        self.logger.debug("CPU resume with hardware breakpoint")
        word_address = int(address//2)
        self.device.avr.protocol.run_to(word_address)

    def stack_pointer_read(self):
        """
        Reads the stack pointer

        :returns: Stack pointer
        :rtype: bytearray
        """
        self.logger.debug("Reading stack pointer")
        return self.device.avr.stack_pointer_read()

    def status_register_read(self):
        """
        Reads the status register from the AVR

        :return: 8-bit SREG value
        """
        self.logger.debug("Reading status register")
        return self.device.avr.protocol.memory_read(Avr8Protocol.AVR8_MEMTYPE_OCD, Avr8Protocol.AVR8_MEMTYPE_OCD_SREG, 1)

    def program_counter_read(self):
        """
        Reads the program counter register from the AVR

        :return: PC value as word address
        """
        self.logger.debug("Reading program counter")
        return self.device.avr.protocol.program_counter_read()

    def program_counter_write(self, program_counter):
        """
        Write a new program counter value (word) to the AVR

        :param program_counter: new PC value to write (word address)
        """
        self.logger.debug("Writing program counter to %X", program_counter)
        self.device.avr.protocol.program_counter_write(program_counter)

    def register_file_read(self):
        """
        Reads out the AVR register file (R0::R31)

        :return: 32 bytes of register file content as bytearray
        """
        self.logger.debug("Reading register file")
        return self.device.avr.protocol.regfile_read()

    def register_file_write(self, regs):
        """
        Writes the AVR register file (R0::R31)

        :param data: 32 byte register file content as bytearray
        :raises ValueError: if 32 bytes are not given
        """
        self.logger.debug("Writing register file")
        return self.device.avr.protocol.regfile_write(regs)

    def sram_read(self, address, numbytes):
        """
        Read SRAM content from the AVR

        :param address: absolute address to start reading from
        :param numbytes: number of bytes to read
        """
        self.logger.debug("Reading %d bytes from SRAM at %X", numbytes, address)
        # The debugger protocols (via pymcuprog) use memory-types with zero-offsets
        # So the offset is subtracted here (and added later in the debugger)
        offset = (self.memory_info.memory_info_by_name('internal_sram'))['address']
        return self.device.read(self.memory_info.memory_info_by_name('internal_sram'), address-offset, numbytes)

    def sram_write(self, address, data):
        """
        Write SRAM content to the AVR

        :param address: absolute address in SRAM to start writing
        :param data: content to store to SRAM
        """
        self.logger.debug("Writing %d bytes to SRAM at %X", len(data), address)
        # The debugger protocols (via pymcuprog) use memory-types with zero-offsets
        # So the offset is subtracted here (and added later in the debugger)
        offset = (self.memory_info.memory_info_by_name('internal_sram'))['address']
        return self.device.write(self.memory_info.memory_info_by_name('internal_sram'), address-offset, data)

    def flash_read(self, address, numbytes):
        """
        Read flash content from the AVR

        :param address: absolute address to start reading from
        :param numbytes: number of bytes to read
        """
        self.logger.debug("Reading %d bytes from flash at %X", numbytes, address)
        # The debugger protocols (via pymcuprog) use memory-types with zero-offsets
        # However the address used here is already zero-offset, so no compensation is done here
        return self.device.read(self.memory_info.memory_info_by_name('flash'), address, numbytes)

    def eeprom_read(self, address, numbytes):
        """
        Read EEPROM content from the AVR

        :param address: absolute address to start reading from
        :param numbytes: number of bytes to read
        """
        self.logger.debug("Reading %d bytes from EEPROM at %X", numbytes, address)
        # The debugger protocols (via pymcuprog) use memory-types with zero-offsets
        # So the offset is subtracted here (and added later in the debugger)
        offset = (self.memory_info.memory_info_by_name('eeprom'))['address']
        return self.device.read(self.memory_info.memory_info_by_name('eeprom'), address-offset, numbytes)

    def eeprom_write(self, address, data):
        """
        Write EEPROM content to the AVR

        :param address: absolute address in EEPROM to start writing
        :param data: content to store to EEPROM
        """
        self.logger.debug("Writing %d bytes to EEPROM at %X", len(data), address)
        # The debugger protocols (via pymcuprog) use memory-types with zero-offsets
        # So the offset is subtracted here (and added later in the debugger)
        offset = (self.memory_info.memory_info_by_name('eeprom'))['address']
        return self.device.write(self.memory_info.memory_info_by_name('eeprom'), address-offset, data)

    def hardware_breakpoint_set(self, address):
        """
        Sets a hardware breakpoint in the AVR OCD

        :param address: byte address to set hardware breakpoint
        """
        self.logger.debug("Setting hardware breakpoint at %X", address)
        self.device.avr.breakpoint_set(address)

    def hardware_breakpoint_clear(self):
        """
        Clears the hardware breakpoint in the AVR OCD
        """
        self.logger.debug("Clearing hardware breakpoint")
        self.device.avr.breakpoint_clear()

    def software_breakpoint_set(self, address):
        """
        Sets a software breakpoint in the AVR flash

        :param address: byte address to set software breakpoint
        """
        self.logger.debug("Setting software breakpoint at %X", address)
        self.device.avr.protocol.software_breakpoint_set(address)

    def software_breakpoint_clear(self, address):
        """
        Clears a software breakpoint in the AVR flash and restores the original instruction

        :param address: byte address to remove software breakpoint
        """
        self.logger.debug("Clearing software breakpoint")
        self.device.avr.protocol.software_breakpoint_clear(address)

    def software_breakpoint_clear_all(self):
        """
        Removes all software breakpoints immediately and restores flash to its original content
        """
        self.logger.debug("Clearing all software breakpoints")
        self.device.avr.protocol.software_breakpoint_clear_all()

    def poll_event(self):
        """
        Poll for events from the debugger
        Events are used to signal AVR core transitions from RUN mode to STOPPED mode
        """
        # Check for incoming events
        event = self.device.avr.protocol.poll_events()
        if event:
            # Check if this is a break event
            program_counter = self.device.avr.protocol.decode_break_event(event)
            return program_counter
        return None

    def flush_events(self):
        """
        Flushes all incoming events before or after a session
        """
        while True:
            if not self.device.avr.protocol.poll_events():
                return
