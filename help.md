# pymcuprog - Python MCU programmer
pymcuprog is a Python utility for programming various Microchip MCU devices using Microchip CMSIS-DAP based debuggers

# Usage
pymcuprog is used as a command line interface:

```
pymcuprog [switches] action
```

## Actions (commands)
The only manadatory positional argument specifies the _action_:

### Memory access actions
Read the device ID or signature:

Also functions as a 'connectivity check'
```
ping
```
Read memories from a device:
```
read
```
Write memories to a device:

NB: Does NOT erase before write!
```
write
```
Erase memories on a device:
```
erase
```
Read out memories from a device and compare:
```
verify
```

### Voltage-related actions
Read the actual (sampled) VTG voltage from a kit or debugger:
```
getvoltage
```
Read the supply voltage set-point from a kit or debugger:
```
getsupplyvoltage
```
Set the supply voltage set-point from a kit or debugger:

Use -l literal to specify voltage
```
setsupplyvoltage
```
Read the USB voltage from a kit or debugger:
```
getusbvoltage
```

### Other misc actions
Reset the application (by entering and leaving programming mode):
```
reset
```
Reboot the debugger:
```
reboot-debugger
```
Convert Intel® hex file to UF2 file
```
makeuf2
```

## Memory types
Memory types may vary depending on the device in question.

Specify the memory type using -m MEMORY or --memory MEMORY

# Supported memory types
```
calibration_row
config_words
eeprom
flash
fuses
icd
internal_sram
lockbits
signatures
user_id
user_row
dia
dci
```

## Optional arguments and switches

### Administrative arguments
```
-h, --help
    show this help message and exit

-V, --version
    Print pymcuprog version number and exit

-R, --release-info
    Print pymcuprog release details and exit
```

### General arguments
```
-d DEVICE, --device DEVICE
    device to program

-p PACKPATH, --packpath PACKPATH
    path to pack (DFP) to use - mandatory for any action when using a PIC device.
    Packs can be installed usign MPLABX Pack Manager (use Tools->Packs)
    Pack path is displayed in the status bar.
    Packs can be downloaded and unzipped from https://packs.download.microchip.com/

-t TOOL, --tool TOOL
    tool to connect to
    supported tools include:
    - uart (for serialUPDI).  Use -u argument to specify which serial port to use.
    - nedbg (PKOB nano / debugger on Curiosity Nano)
    - pickit4
    - snap
    - atmelice
    - powerdebugger
    - edbg (debugger on Xplained Pro/Ultra)
    - medbg (debugger on Xplained Mini/Nano)
    - JTAGICE3 (firmware version 3.0 or newer)

-s SERIALNUMBER, --serialnumber SERIALNUMBER
    USB serial number of the unit to use

-v {debug,info,warning,error,critical},
--verbose {debug,info,warning,error,critical}
    Logging verbosity level

-x, --timing
    add timing output
```

### Memory access arguments
```
-o OFFSET, --offset OFFSET
    memory byte offset to access
    Defaults to 0 (start of memory section)
    Only applies to literal and binary-file operations

-b BYTES, --bytes BYTES
    number of bytes to read
    Ignored for write operations (cannot be used to truncate a write)
    Defaults to entire memory section size
    Requires that a memory section is specified

-l LITERAL [LITERAL ...], --literal LITERAL [LITERAL ...]
    literal value(s) to write

-f FILENAME, --filename FILENAME
    file to write / read.

    A specified filename which has .hex extension will be treated as Intel hex
    format; all other file extensions are treated as binary files.

    When writing from a .hex file, the memory segment addresses are read from
    the file, so the OFFSET argument is not allowed.

    When reading to an Intel hex file, only eeprom, flash, fuses, config_words,
    and user_row memories will be written

    Hex file offsets are actual memory section locations for PIC and SAM devices.
    AVR device offsets in hex files are (handled by the toolchain):
    - flash 0x000000
    - eeprom 0x810000
    - fuses 0x820000
    - lockbits 0x830000
    - signatures 0x840000
    - user signatures 0x850000

--verify
    verify content after write (by readback and compare)

--erase
    erase device before write (equivalent to pymcuprog erase)
    This switch is valid only when writing from an Intel hex file.
    A chip erase / bulk erase will be executed before write - note that not all memories will be erased:
    for example EEPROM may be preserved on AVR devices if the EESAVE fuse bit is set.
```
### Programming interface arguments
```
-i INTERFACE, --interface INTERFACE
    Programming interface to use

-c CLK, --clk CLK
    clock frequency in Hz or baud rate in bps for programming interface.
    (eg: '-c 32768' or '-c 115k' or '-c 1M')

-u UART, --uart UART
    UART to use for serialUPDI tool (when using -t uart)
```

### Special-function UPDI arguments
```
-H {tool-toggle-power,user-toggle-power,simple-unsafe-pulse},
--high-voltage {tool-toggle-power,user-toggle-power,simple-unsafe-pulse}
    UPDI high-voltage activation mode

-U, --user-row-locked-device
    Writes the User Row on a locked device

-C, --chip-erase-locked-device
    Execute a Chip Erase on a locked device
```

### Utility arguments
```
--uf2file UF2FILE
    Name of UF2 file to generate
```

# Examples
Examples of using pymcuprog:
```
# Ping a device on a kit (checks connectivity by reading its signature):
pymcuprog ping

# Ping a device using Atmel-ICE (standalone debugger requires more information):
pymcuprog ping -t atmelice -d atmega4809 -i updi

# Erase and program memories from an Intel hex file using PICkit4:
pymcuprog write -t pickit4 -d atmega4809 -i updi -f myfile.hex --erase

# Read 64 bytes of flash from offset 0x80 in flash memory space:
pymcuprog read -m flash -o 0x80 -b 64

# Write literal values 0x01, 0x02 to EEPROM at offset 16 on a kit:
pymcuprog write -m eeprom -o 16 -l 0x01 0x02

# Write fuse byte 1 to 0xE0 on a kit:
pymcuprog write -m fuses -o 1 -l 0xE0

# Erase a device on a kit:
pymcuprog erase

# Erase a locked device on a kit (UPDI only):
pymcuprog erase --chip-erase-locked-device

# Reset a device on a kit (by entering and leaving programming mode):
pymcuprog reset

# Read the actual (sampled) VTG voltage from a kit or debugger:
pymcuprog getvoltage

# Set target supply voltage on a kit (voltage provided by -l literal argument):
pymcuprog setsupplyvoltage -l 3.3

# Convert Intel hex file to UF2 file (--uf2file argument is optional)
pymcuprog makeuf2 -f myfile.hex --uf2file newfile.uf2
```
# serialUPDI usage
SerialUPDI (also known as 'pyupdi') is implemented as a _tool_ in pymcuprog.

To use it:
- connect a resistor between a serial port adapter's RX, TX and the UPDI pin as shown in the [readme](./README.md)
- specify uart tool using the switch: '--tool uart'
- specify which serial port to use using the switch '--uart {serialport}'
- optionally specify the baud rate using the switch '--clk {baud}'
- optionally specify the uart read timeout using the switch '--uart-timeout {timeout}'
- use the basic actions for accessing memories as shown above

Example:
```
# Ping a device using serialUPDI:
pymcuprog ping -t uart -u COM42 -d atmega4809

# Erase a device using serialUPDI:
pymcuprog erase -t uart -u COM42 -d atmega4809

# Erase and program memories from an Intel hex file using serialUPDI:
pymcuprog write -t uart -u COM42 -d atmega4809 -f myfile.hex --erase
```