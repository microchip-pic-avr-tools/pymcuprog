"""
NVM layer protocols
"""
# Python 3 compatibility for Python 2
from __future__ import print_function
from logging import getLogger

from .deviceinfo.deviceinfokeys import DeviceInfoKeys
from .pymcuprog_errors import PymcuprogSessionConfigError
from .toolconnection import ToolSerialConnection

def get_nvm_access_provider(transport, device_info, interface="", packpath=None, frequency=None, options=""):
    """
    Returns an NVM provider with the requested properties

    :param transport: Transport layer object
    :param device_info: Device info dict
    :param interface: Physical interface for NVM
    :param packpath: Path to pack
    :param frequency: Interface clock
    :param options: Special options
    :return: NVM access object
    """
    # Although it is considered best practice to have imports at top level, in this case it makes sense to have the
    # imports on the function level as in most cases only one import will be used.  Having all imports at the top
    # level will then be a waste of resources.
    #pylint: disable=import-outside-toplevel
    # There will be cyclic imports since the modules imported below containing NVM Access providers will import
    # from the current module since all NVM Access providers inherits from the NVM Access provider base classes
    # defined in the current module, but this should be ok since the imports below are late.
    #pylint: disable=cyclic-import
    accessprovider = None
    architecture = device_info[DeviceInfoKeys.ARCHITECTURE].lower()
    if not interface and DeviceInfoKeys.INTERFACE in device_info:
        interface = device_info[DeviceInfoKeys.INTERFACE].lower()

    if architecture in ['pic16', 'pic18', 'pic24', 'dspic33']:
        from .nvmpic import NvmAccessProviderCmsisDapPic
        accessprovider = NvmAccessProviderCmsisDapPic(transport, device_info, packpath, options=options)

    elif architecture == 'avr8x':
        if isinstance(transport, ToolSerialConnection):
            if interface == 'updi':
                from .nvmserialupdi import NvmAccessProviderSerial
                accessprovider = NvmAccessProviderSerial(transport, device_info, options=options)
        elif interface == 'updi':
            from .nvmupdi import NvmAccessProviderCmsisDapUpdi
            accessprovider = NvmAccessProviderCmsisDapUpdi(transport, device_info=device_info,
                                                           frequency=frequency, options=options)
    elif architecture == 'avr8':
        if interface == 'isp':
            from .nvmspi import NvmAccessProviderCmsisDapSpi
            accessprovider = NvmAccessProviderCmsisDapSpi(transport, device_info)
        elif interface == "debugwire":
            from .nvmdebugwire import NvmAccessProviderCmsisDapDebugwire
            accessprovider = NvmAccessProviderCmsisDapDebugwire(transport, device_info)
        elif interface == "jtag":
            from .nvmmegaavrjtag import NvmAccessProviderCmsisDapMegaAvrJtag
            accessprovider = NvmAccessProviderCmsisDapMegaAvrJtag(transport, device_info)
        else:
            raise PymcuprogSessionConfigError("Interface not specified: use --interface [isp | jtag | debugwire]")
    elif architecture == "xmega":
        if interface == "pdi":
            from .nvmxmega import NvmAccessProviderCmsisDapXmega
            accessprovider = NvmAccessProviderCmsisDapXmega(transport, device_info)
    elif architecture == "avrtinytiny":
        if interface == "tpi":
            from .nvmtpi import NvmAccessProviderCmsisDapTpi
            accessprovider = NvmAccessProviderCmsisDapTpi(transport, device_info)
    elif architecture == 'cortex-m0plus':
        from .nvmmzeroplus import NvmAccessProviderCmsisDapMZeroPlus
        accessprovider = NvmAccessProviderCmsisDapMZeroPlus(transport, device_info, frequency)
    elif architecture == 'avr32':
        from .nvmavr32 import NvmAccessProviderCmsisDapAvr32
        accessprovider = NvmAccessProviderCmsisDapAvr32(transport, device_info)

    return accessprovider

class NvmAccessProvider:
    """
    Wrapper for device info
    """

    def __init__(self, device_info):
        self.device_info = device_info
        self.logger = getLogger(__name__)

    def _log_incomplete_stack(self, device_stack, beta=False):
        """
        Used to tell the user this device stack is not completed yet

        :param device_stack: User friendly name of target stack
        :param beta: Suppress warnings for beta stacks - info loglevel is used for beta.
        """
        if beta:
            self.logger.info("%s stack is in Beta state", device_stack)
        else:
            self.logger.warning("")
            self.logger.warning("%s stack is in Alpha state", device_stack)
            self.logger.warning("Expect some features to be missing")
            self.logger.warning("")

    def start(self, user_interaction_callback=None):
        """
        Start (activate) session

        :param user_interaction_callback: Callback to be called when user interaction is required,
            for example when doing UPDI high-voltage activation with user target power toggle.
            This function could ask the user to toggle power and halt execution waiting for the user
            to respond (this is default behavior if the callback is None), or if the user is another
            script it could toggle power automatically and then return.
        """
        #pylint: disable=unused-argument
        self.logger.debug("No specific initializer for this provider")

    def stop(self):
        """
        Stop (deactivate) session
        """
        self.logger.debug("No specific de-initializer for this provider")

    def hold_in_reset(self):
        """
        Hold target in reset
        """
        self.logger.debug("hold_in_reset not implemented for this provider")

    def release_from_reset(self):
        """
        Release target from reset
        """
        self.logger.debug("release_from_reset not implemented for this provider")

class NvmAccessProviderCmsisDapTool(NvmAccessProvider):
    """
    General CMSIS-DAP Tool
    """

    def __init__(self, device_info):
        NvmAccessProvider.__init__(self, device_info)


class NvmAccessProviderCmsisDapAvr(NvmAccessProviderCmsisDapTool):
    """
    AVR CMSIS DAP Tool
    """

    def __init__(self, device_info):
        NvmAccessProviderCmsisDapTool.__init__(self, device_info)
