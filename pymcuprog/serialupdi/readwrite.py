"""
Read/write access provider for UPDI
"""
from logging import getLogger
from pymcuprog.pymcuprog_errors import PymcuprogSerialUpdiProtocolError
from . import constants


class UpdiReadWrite(object):
    """
    Provides various forms of reads and writes for UPDI applications
    Makes us of the datalink provided
    """

    def __init__(self, datalink):
        self.logger = getLogger(__name__)
        self.datalink = datalink

    def read_cs(self, address):
        """
        Read from Control/Status space

        :param address: address (index) to read
        :type address: int
        :return: value read
        :rtype: byte
        """
        return self.datalink.ldcs(address)

    def write_cs(self, address, value):
        """
        Write to Control/Status space

        :param address: address (index) to write
        :type address: int
        :param value: 8-bit value to write
        :type value: byte
        """
        return self.datalink.stcs(address, value)

    def write_key(self, size, key):
        """
        Write a KEY into UPDI

        :param size: size of key to send
        :type size: int
        :param key: key value
        :type: key bytearray
        """
        return self.datalink.key(size, key)

    def read_sib(self):
        """
        Read the SIB from UPDI

        :return: SIB string read
        :rtype: bytearray
        """
        return self.datalink.read_sib()

    def read_byte(self, address):
        """
        Read a single byte from UPDI

        :param address: address to read from
        :type address: int
        :return: value read
        :rtype: byte
        """
        return self.datalink.ld(address)

    def write_byte(self, address, value):
        """
        Writes a single byte to UPDI

        :param address: address to write to
        :type address: int
        :param value: value to write
        :type value: byte
        """
        return self.datalink.st(address, value)

    def read_data(self, address, size):
        """
        Reads a number of bytes of data from UPDI

        :param address: address to write to
        :type address: int
        :param size: number of bytes to read
        :type size: int
        """
        self.logger.debug("Reading %d bytes from 0x%04X", size, address)
        # Range check
        if size > constants.UPDI_MAX_REPEAT_SIZE:
            raise PymcuprogSerialUpdiProtocolError("UPDI cannot read {} bytes in one go".format(size))

        # Store the address
        self.datalink.st_ptr(address)

        # Fire up the repeat
        if size > 1:
            self.datalink.repeat(size)

        # Do the read(s)
        return self.datalink.ld_ptr_inc(size)

    def read_data_words(self, address, words):
        """
        Reads a number of words of data from UPDI

        :param address: address to write to
        :type address: int
        :param words: number of words to read
        :type words: int
        """
        self.logger.debug("Reading %d words from 0x%04X", words, address)

        # Range check
        if words > constants.UPDI_MAX_REPEAT_SIZE >> 1:
            raise PymcuprogSerialUpdiProtocolError("UPDI cannot read {} words in one go".format(words))

        # Store the address
        self.datalink.st_ptr(address)

        # Fire up the repeat
        if words > 1:
            self.datalink.repeat(words)

        # Do the read
        return self.datalink.ld_ptr_inc16(words)

    def write_data_words(self, address, data):
        """
        Writes a number of words to memory

        :param address: address to write to
        :type address: int
        :param data: data to write
        :type data: list of bytes
        """
        numbytes = len(data)
        # Special-case of 1 word
        if numbytes == 2:
            value = data[0] + (data[1] << 8)
            return self.datalink.st16(address, value)

        # Range check
        if numbytes > constants.UPDI_MAX_REPEAT_SIZE << 1:
            raise PymcuprogSerialUpdiProtocolError("UPDI cannot write {} bytes in one go".format(numbytes))

        # Store the address
        self.datalink.st_ptr(address)

        # Fire up the repeat
        self.datalink.repeat(numbytes >> 1)
        return self.datalink.st_ptr_inc16(data)

    def write_data(self, address, data):
        """
        Writes a number of bytes to memory

        :param address: address to write to
        :type address: int
        :param data: data to write
        :type data: list of bytes
        """
        numbytes = len(data)
        # Special case of 1 byte
        if numbytes == 1:
            return self.datalink.st(address, data[0])
        # Special case of 2 byte
        if numbytes == 2:
            self.datalink.st(address, data[0])
            return self.datalink.st(address + 1, data[1])

        index = 0
        while numbytes:
            if numbytes > constants.UPDI_MAX_REPEAT_SIZE:
                chunk_size = constants.UPDI_MAX_REPEAT_SIZE
            else:
                chunk_size = numbytes

            # Store the address
            self.datalink.st_ptr(address)

            # Fire up the repeat
            self.datalink.repeat(chunk_size)
            self.datalink.st_ptr_inc(data[index:index+chunk_size])

            index += chunk_size
            address += chunk_size
            numbytes -= chunk_size

