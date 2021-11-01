"""
Harvester scripts

Currently only supports AVR atdf files
"""
# Python 3 compatibility for Python 2
from __future__ import print_function

import argparse
import textwrap
from xml.etree import ElementTree

from pymcuprog.deviceinfo.memorynames import MemoryNames
from pymcuprog.deviceinfo.deviceinfokeys import DeviceMemoryInfoKeys, DeviceInfoKeysAvr

def map_atdf_memory_name_to_pymcuprog_name(atdf_name):
    """
    Mapping a memory name in atdf files to the corresponding memory name used in the pymcuprog device models

    :param atdf_name: Name of memory in atdf files
    :return: Name of memory in pymcuprog device models
    """
    pymcuprog_name = 'unknown'
    if atdf_name == 'progmem':
        pymcuprog_name = MemoryNames.FLASH
    if atdf_name == 'user_signatures':
        # Datasheets actually use user_row for UPDI devices at least
        pymcuprog_name = MemoryNames.USER_ROW
    if atdf_name == 'eeprom':
        pymcuprog_name = MemoryNames.EEPROM
    if atdf_name == 'fuses':
        pymcuprog_name = MemoryNames.FUSES
    if atdf_name == 'lockbits':
        pymcuprog_name = MemoryNames.LOCKBITS
    if atdf_name == 'signatures':
        pymcuprog_name = MemoryNames.SIGNATURES
    if atdf_name == 'internal_sram':
        pymcuprog_name = MemoryNames.INTERNAL_SRAM

    return pymcuprog_name

def determine_chiperase_effect(name, architecture):
    if 'avr' in architecture:
        if name in ['user_signatures', 'fuses', 'signatures', 'internal_sram']:
            return('ChiperaseEffect.NOT_ERASED')
        elif name in ['lockbits', 'progmem']:
            return('ChiperaseEffect.ALWAYS_ERASED')
        elif name in ['eeprom']:
            return('ChiperaseEffect.CONDITIONALLY_ERASED_AVR')
    else:
        return('# To be filled in manually')

def determine_isolated_erase(name, architecture):
    if 'avr' in architecture:
        if 'avr8x' in architecture and name in ['progmem']:
            # UPDI devices now supports isolated erase for flash
            return('True')
        if name in ['user_signatures', 'eeprom']:
            return('True')
        elif name in ['internal_sram', 'lockbits', 'progmem', 'fuses', 'signatures']:
            return('False')
    else:
        return('# To be filled in manually')

def determine_write_size(memory_name, page_size, device_name):
    write_size = 1
    device_name = device_name.lower()
    if memory_name == 'flash':
        if (device_name.find('avr') != -1 and ((device_name.find('da') != -1) or (device_name.find('db') != -1))):
            write_size = 2
        else:
            write_size = page_size
    if memory_name == "user_row":
        if device_name.find('avr') != -1 and device_name.find('ea') != -1:
            # For AVR EA user row the complete page must be written
            write_size = page_size
    elif memory_name == 'signatures':
        write_size = 0
    return write_size


def capture_memory_attribute(attribute, architecture, device_name):
    """
    Capture the memory attribute

    :param attribute: memory attribute to capture
    :return: attributes found as a string
    """
    name = attribute['name'].lower()
    size = attribute['size']
    start = attribute['start']

    try:
        pagesize = attribute['pagesize']
    except KeyError:
        pagesize = '1'
    # For some AVRs the ATDF gives a pagesize of fuses and lockbits equal to flash or EEPROM page size but fuses and lockbits are always byte accessible.
    if name in ['fuses', 'lockbits']:
        pagesize = '1'
    # Read size is always 1 byte except for flash that can only read complete words
    readsize = 1
    if name in ['progmem']:
        readsize = 2
    output = ""
    # These names are the names used in the atdf files and might differ from the pymcuprog MemoryNames
    if name in ['progmem', 'eeprom', 'user_signatures', 'fuses', 'lockbits', 'signatures', 'internal_sram']:
        print_name = map_atdf_memory_name_to_pymcuprog_name(name)
        output += "\n    # {}\n".format(print_name)
        output += capture_field('{}_{}_byte'.format(print_name, DeviceMemoryInfoKeys.ADDRESS), start)
        output += capture_field('{}_{}_bytes'.format(print_name, DeviceMemoryInfoKeys.SIZE), size)
        output += capture_field('{}_{}_bytes'.format(print_name, DeviceMemoryInfoKeys.PAGE_SIZE), pagesize)
        # These are the same for all AVRs
        output += "    '{}_{}_bytes': {},\n".format(print_name, DeviceMemoryInfoKeys.READ_SIZE, readsize)
        output += "    '{}_{}_bytes': {},\n".format(print_name, DeviceMemoryInfoKeys.WRITE_SIZE, determine_write_size(print_name, pagesize, device_name))
        output += "    '{}_{}': {},\n".format(print_name, DeviceMemoryInfoKeys.CHIPERASE_EFFECT, determine_chiperase_effect(name, architecture))
        output += "    '{}_{}': {},\n".format(print_name, DeviceMemoryInfoKeys.ISOLATED_ERASE, determine_isolated_erase(name, architecture))
    return output


def capture_register_offset(name, offset):
    """
    Wrapper to create a string definition

    :param name: register name
    :param offset: register offset
    :return: string of register and offset
    """
    return capture_field("{}_base".format(name.lower()), offset)


def capture_field(field, value):
    """
    Macro to create text format field

    :param field: register name
    :param value: register value
    :return: string of definition
    """
    try:
        _test_value = int(value, 16)
    except (ValueError, AttributeError):
        # Can't convert string to int, assumed to be string
        return "    '{}': '{}',\n".format(field, value)
    return "    '{}': {},\n".format(field, value)

def capture_device_element(element, device_name):
    """
    Capture data from a device element

    :param element: element with tag='device'
    :return: captured data from the device element as a string
    """
    architecture = element.attrib['architecture'].lower()
    output = capture_field('name', element.attrib['name'].lower())
    output += capture_field('architecture', architecture)
    for i in element.iterfind("address-spaces/address-space/memory-segment"):
        output += capture_memory_attribute(i.attrib, architecture, device_name)
    output += "\n    # Some extra AVR specific fields\n"
    return output

def capture_module_element(element):
    """
    Capture data from a module element

    This function will return data captured from the module element but will also check if the module
    element contains info about an UPDI fuse (fuse to configure a shared UPDI pin)

    :param element: element with tag='module'
    :return: tuple of
    * output - captured module element data as a string
    * found_updi_fuse - True if the module element contained info about an UPDI fuse
    """
    output = ""
    found_updi_fuse = False
    for i in element.iterfind("instance/register-group"):
        name = i.attrib['name']
        offset = "0x{:08X}".format(int(i.attrib['offset'], 16))
        if i.attrib['name'] == 'SYSCFG':
            output += capture_register_offset(name, offset)
            output += capture_register_offset('OCD', "0x{:08X}".format(int(offset, 16) + 0x80))
        if i.attrib['name'] == 'NVMCTRL':
            output += capture_register_offset(name, offset)
    for i in element.iterfind("instance/signals/signal"):
        if i.attrib['group'] == 'UPDI' and i.attrib['pad'] is not None:
            output += capture_field('prog_clock_khz', '900')
            found_updi_fuse = True
    return output, found_updi_fuse

def capture_signature_from_property_groups_element(element):
    """
    Capture signature (Device ID) data from a property-group element

    :param element: element with tag='property-groups'
    :return: bytearray with 3 bytes of Device ID data
    """
    signature = bytearray(3)
    for i in element.findall('property-group/property'):
        if i.attrib['name'] == 'SIGNATURE0':
            signature[0] = int(i.attrib['value'], 16)
        if i.attrib['name'] == 'SIGNATURE1':
            signature[1] = int(i.attrib['value'], 16)
        if i.attrib['name'] == 'SIGNATURE2':
            signature[2] = int(i.attrib['value'], 16)
    return signature

def get_flash_offset(element):
    flash_offset = "0x00000000"
    for i in element.iterfind("property-group/property"):
        if i.attrib['name'] == 'PROGMEM_OFFSET':
            flash_offset = i.attrib['value']
    return flash_offset

def correct_flash_offset(data_string, offset):
    corrected_data_string = ''
    ind = data_string.find("'flash_address_byte': ")
    corrected_data_string += data_string[:ind+22]
    corrected_data_string += offset
    corrected_data_string += data_string[ind+22+10:]
    return corrected_data_string

def determine_address_size(progmem_offset):
    address_size = '16-bit'
    if progmem_offset is not None:
        progmem_offset = int(progmem_offset, 16)
        if progmem_offset > 0xFFFF:
            address_size = '24-bit'
    return address_size

def harvest_from_file(filename):
    """
    Harvest parameters from a file

    :param filename: path to file to parse
    :return: list of parameters
    """
    xml_iter = ElementTree.iterparse(filename)
    output = ""
    module_output = ""
    shared_updi = False
    progmem_offset = None
    for event, elem in xml_iter:
        if event == 'end':
            if elem.tag == 'device':
                device_name = elem.attrib['name']
                output += capture_device_element(elem, device_name)
            if elem.tag == 'module':
                module, found_updi_fuse = capture_module_element(elem)
                module_output += module
                if found_updi_fuse:
                    shared_updi = True
            if elem.tag == 'interface':
                output += capture_field(elem.tag, elem.attrib['name'])
            if elem.tag == 'property-groups':
                signature = capture_signature_from_property_groups_element(elem)
                progmem_offset = get_flash_offset(elem)

    output += capture_field('address_size', determine_address_size(progmem_offset))
    if not shared_updi:
        output += capture_field(DeviceInfoKeysAvr.PROG_CLOCK_KHZ, '1800')
    output += capture_field(DeviceInfoKeysAvr.DEVICE_ID,
                            "0x{:02X}{:02X}{:02X}".format(signature[0], signature[1], signature[2]))

    # Replace "flash start" with "progmem_offset"
    if progmem_offset:
        output = correct_flash_offset(output, progmem_offset)
    # Append additional module info at the end
    output += module_output
    return output

def main():
    """
    Main function for the harvest utility
    """
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=textwrap.dedent('''\
    Harvests device data from a device data file (.atdf) for one device.

    The harvested data can be used to populate a device file in deviceinfo.devices
        '''))

    parser.add_argument("filename",
                        help="name (and path) of file to harvest data from"
                        )

    arguments = parser.parse_args()

    dict_content = harvest_from_file(arguments.filename)
    content = "\nfrom pymcuprog.deviceinfo.eraseflags import ChiperaseEffect\n\n"
    content += "DEVICE_INFO = {{\n{}}}".format(dict_content)
    print(content)

if __name__ == "__main__":
    main()
