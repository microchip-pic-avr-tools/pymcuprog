"""
This module includes wrapper classes for Tool connection parameters
"""

from .serialupdi.physical import DEFAULT_SERIALUPDI_BAUD

#pylint: disable=too-few-public-methods
class ToolConnection(object):
    """
    Base class for ToolConnection classes used to wrap configuration parameters for tool connections
    """

#pylint: disable=too-few-public-methods
class ToolUsbHidConnection(ToolConnection):
    """
    Helper class wrapping configuration parameters for a connection to a USB HID tool
    """
    serialnumber = None
    tool_name = None

    def __init__(self, serialnumber=None, tool_name=None):
        """
        :param tool_name: Tool name as given in USB Product string.  Some shortnames are also supported
            as defined in pyedbglib.hidtransport.toolinfo.py.  Set to None if don't care
        :param serialnumber: USB serial number string.  Set to None if don't care
        """
        self.serialnumber = serialnumber
        self.tool_name = tool_name

#pylint: disable=too-few-public-methods
class ToolSerialConnection(ToolConnection):
    """
    Helper class wrapping configuration parameters for a connection to a serial port
    """
    serialport = None

    def __init__(self, serialport="COM1", baudrate=DEFAULT_SERIALUPDI_BAUD, timeout=None):
        """
        :param serialport: Serial port name to connect to.
        :type serialport: str
        :param baudrate: baud rate in bps to use for communications
        :type baudrate: int (defaults to 115200)
        :param timeout: timeout value for serial reading.
            When UPDI is not enabled, attempting to read will return after this timeout period.
        :type timeout: float
        """
        self.serialport = serialport
        self.baudrate = baudrate
        self.timeout = timeout
