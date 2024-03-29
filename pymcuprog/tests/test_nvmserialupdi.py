#pylint: disable=too-many-lines
#pylint: disable=too-many-public-methods
#pylint: disable=missing-docstring

import unittest
from mock import MagicMock
from mock import patch

from pymcuprog.nvmserialupdi import NvmAccessProviderSerial
from pymcuprog.deviceinfo import deviceinfo
from pymcuprog.pymcuprog_errors import PymcuprogSessionError
from pymcuprog.toolconnection import ToolSerialConnection

class TestNvmAccessProviderSerial(unittest.TestCase):
    def _mock_updiapplication(self):
        """
        Create a mock of the UpdiApplication instance in pymcuprog.nvmserialupdi

        :returns: Mock of UpdiApplication instance
        """
        mock_updiapplication_patch = patch("pymcuprog.nvmserialupdi.UpdiApplication")
        self.addCleanup(mock_updiapplication_patch.stop)
        mock_updiapplication = mock_updiapplication_patch.start()
        mock_updiapplication_instance = MagicMock()
        mock_updiapplication.return_value = mock_updiapplication_instance

        return mock_updiapplication_instance

    def test_read_device_id_returns_bytearray_with_raw_id(self):
        # Expected ID must match mega4809 as BE24
        id_expected = bytearray([0x1E, 0x96, 0x51])
        id_expected.reverse()

        mock_updiapplication_instance = self._mock_updiapplication()
        mock_updiapplication_instance.read_data.return_value = bytearray([id_expected[2],
                                                                          id_expected[1],
                                                                          id_expected[0]])

        connection = ToolSerialConnection()
        dinfo = deviceinfo.getdeviceinfo('atmega4809')

        serial = NvmAccessProviderSerial(connection, dinfo, None)

        id_read = serial.read_device_id()

        # Check normal path
        self.assertEqual(id_expected, id_read)

        # Check that an exception is raised on unexpected ID
        mock_updiapplication_instance.read_data.return_value = bytearray([0, 0, 0])

        with self.assertRaises(PymcuprogSessionError):
            id_read = serial.read_device_id()

    def test_hold_in_reset_does_nothing(self):
        mock_updiapplication = self._mock_updiapplication()

        connection = ToolSerialConnection()
        dinfo = deviceinfo.getdeviceinfo('atmega4809')
        serial = NvmAccessProviderSerial(connection, dinfo, None)
        serial.hold_in_reset()

        mock_updiapplication.hold_in_reset.assert_not_called()

    def test_release_from_reset_leaves_progmode(self):
        mock_updiapplication = self._mock_updiapplication()

        connection = ToolSerialConnection()
        dinfo = deviceinfo.getdeviceinfo('atmega4809')
        serial = NvmAccessProviderSerial(connection, dinfo, None)
        serial.release_from_reset()

        mock_updiapplication.leave_progmode.assert_called()
