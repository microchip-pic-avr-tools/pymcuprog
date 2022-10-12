# pymcuprog - Python MCU programmer
pymcuprog is a utility for programming various Microchip MCU devices using Microchip CMSIS-DAP based debuggers

## Overview
pymcuprog is available:

* install using pip from pypi: https://pypi.org/project/pymcuprog
* browse source code on github: https://github.com/microchip-pic-avr-tools/pymcuprog
* read API documentation on github: https://microchip-pic-avr-tools.github.io/pymcuprog
* read the changelog on github: https://github.com/microchip-pic-avr-tools/pymcuprog/blob/main/CHANGELOG.md

## Usage
pymcuprog can be used as a command-line interface or a library

### Command-line programming
for help, use:
```bash
pymcuprog --help
```

#### Action: ping
checks connectivity by reading the device identity

Example:
```bash
pymcuprog ping
```
#### Action: erase
erases device memories
* use -m to erase only a specified memory region (if available)

Example: chip erase the device
```bash
pymcuprog erase
```
#### Action: write
writes device memories
* use -f for writing from a file, or
* use -l for writing literal values
* use -m to specify memory type for literal writing
* use -o to specify offset for literal writing

Example: writes the content of an Intel(R) hex file to the appropriate memory areas on the device
```bash
pymcuprog write -f app.hex
```
Note: memory is not erased automatically before writing!

Example: erases memories and then writes an Intel hex file:
```bash
pymcuprog write -f app.hex --erase
```

Example: erases memories, writes an Intel hex file and then verifies the content:
```bash
pymcuprog write -f app.hex --erase --verify
```

#### Action: read
reads device memories
* use -m to specify memory type
* use -o to specify offset to read from
* use -b to specify number of bytes to read
* use -f to read to a file

Example: reads 64 bytes of flash memory from offset 0x1000
```bash
pymcuprog read -m flash -o 0x1000 -b 64
```

#### Action: reset
resets the target device

Example:
```bash
pymcuprog reset
```

### Command-line board utilities

#### Action: getvoltage
reads the actual target operating voltage

Example:
```bash
pymcuprog getvoltage
```

#### Action: getsupplyvoltage
reads the supply voltage (set-point)

Example:
```bash
pymcuprog getsupplyvoltage
```

#### Action: getusbvoltage
reads the USB voltage (Vbus)

Example:
```bash
pymcuprog getusbvoltage
```

#### Action: setsupplyvoltage
sets the target supply voltage
* use -l to specify a literal supply voltage value

Example: sets the target supply voltage on a Curiosity Nano kit to 3.3V
```bash
pymcuprog setsupplyvoltage -l 3.3
```

#### Action: reboot-debugger
reboots the debugger

Example: reboots a Curiosity Nano kit
```bash
pymcuprog reboot-debugger
```

### Command-line switches
Many of these switches are optional, and many parameters are automatically set when using a Curiosity Nano or Xplained Pro kit.
* -t TOOL to select which tool to use.  Optional if only one is connected.
* -s SERIALNUMBER to select which tool instance to use.  Optional if only one is connected.
* -d DEVICE to specify the device to program.  Optional when using a kit.
* -i INTERFACE to specify the target communication interface.  Optional.
* -p PACKPATH to specify the path to the DFP for PIC devices*
* -c CLK to specify the programming interface clock speed.  Optional.
* --verify to verify after programming
* -u UART to use native host serial port UART for UPDI instead of a USB-based tool.
* -H MODE to select UPDI high-voltage entry mode ('tool-toggle-power', 'user-toggle-power', 'simple-unsafe-pulse')
* -U to write user row values when the device is locked (UPDI only)
* -C to erase and unlock a locked device (UPDI only)
* -v LEVEL for selecting logging verbosity ('debug', 'info', 'warning', 'error', 'critical')


####
*Notes regarding PACKPATH argument

While pymcuprog itself contains sufficient information to program AVR devices (with UPDI interface), it is unable to program a PIC device without access to programming scripts for that device.  These scripts are deployed in Device Family Packs (DFP) on https://packs.download.microchip.com and are only provided for PIC devices mounted on Curiosity Nano boards or other boards with the PKOB nano (nEDBG) debugger.  To use pymcuprog with PIC devices, you will either need to download a DFP for the PIC in question, or have MPLAB X v5.25 or later installed.  In either case the path to the particular device in the scripts folder inside the DFP must be passed into pymcuprog using the -p PACKPATH argument.  Remember to use "<path>" if the path itself contains spaces.

Example: Ping the device on a PIC16F15244 Curiosity Nano
```bash
pymcuprog ping -p "c:\Program Files (x86)\Microchip\MPLABX\v5.40\packs\Microchip\PIC16F1xxxx_DFP\1.4.119\scripts\pic16f15244"
```

### Serial port UPDI (pyupdi)
The AVR UPDI interface implements a UART protocol, which means that it can be used by simply connecting TX and RX pins of a serial port together with the UPDI pin; with a series resistor (eg: 1k) between TX and UPDI to handle contention.  (This configuration is also known as "pyupdi".)  Be sure to connect a common ground, and use a TTL serial adapter running at the same voltage as the AVR device.

<pre>
                        Vcc                     Vcc
                        +-+                     +-+
                         |                       |
 +---------------------+ |                       | +--------------------+
 | Serial port         +-+                       +-+  AVR device        |
 |                     |      +----------+         |                    |
 |                  TX +------+   1k     +---------+ UPDI               |
 |                     |      +----------+    |    |                    |
 |                     |                      |    |                    |
 |                  RX +----------------------+    |                    |
 |                     |                           |                    |
 |                     +--+                     +--+                    |
 +---------------------+  |                     |  +--------------------+
                         +-+                   +-+
                         GND                   GND
</pre>

pymcuprog includes this implementation as an alternative to USB/EDBG-based tools.  To connect via a serial port, use the "uart" tool type with the UART switch in addition.

Example: checks connectivity by reading the device identity
```bash
pymcuprog ping -d avr128da48 -t uart -u com35
```

When using serial port UPDI it is optional to use:
* --clk BAUD to specify the baud rate (defaults to 115200)
* --uart-timeout TIMEOUT to specify the uart read timeout (defaults to 1.0s)

Increasing the baud rate can decrease programming time.  Decreasing the timeout can decrease the initial connection latency when UPDI is disabled and does not respond.  These parameters can be tweaked to suit the serial port adapter in use.


### Library
pymcuprog can be used as a library using its backend API.  For example:
```python
# pymcuprog uses the Python logging module
import logging
logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.WARNING)

# Configure the session
from pymcuprog.backend import SessionConfig
sessionconfig = SessionConfig("atmega4808")

# Instantiate USB transport (only 1 tool connected)
from pymcuprog.toolconnection import ToolUsbHidConnection
transport = ToolUsbHidConnection()

# Instantiate backend
from pymcuprog.backend import Backend
backend = Backend()

# Connect to tool using transport
backend.connect_to_tool(transport)

# Start the session
backend.start_session(sessionconfig)

# Read the target device_id
device_id = backend.read_device_id()
print ("Device ID is {0:06X}".format(int.from_bytes(device_id, byteorder="little")))
```

## Logging
This package uses the Python logging module for publishing log messages to library users.
A basic configuration can be used (see example), but for best results a more thorough configuration is recommended in order to control the verbosity of output from dependencies in the stack which also use logging.
See logging.yaml which is included in the package (although only used for CLI)

## Dependencies
pymcuprog depends on pyedbglib for its transport protocol.
pyedbglib requires a USB transport library like libusb.  See pyedbglib package for more information.

## Versioning
pymcuprog version can be determined using the CLI:
```bash
pymcuprog -V
```

or using the library:
```python
from pymcuprog.version import VERSION as pymcuprog_version
print("pymcuprog version {}".format(pymcuprog_version))
```

In addition, the CLI-backend API is versioned for convenience:
```python
from pymcuprog.backend import Backend
backend = Backend()
print("pymcuprog backend API version: {}".format(backend.get_api_version()))
```

## Supported devices and tools
pymcuprog is primarily intended for use with PKOB nano (nEDBG) debuggers which are found on Curiosity Nano kits and other development boards.  This means that it is continuously tested with a selection of AVR devices with UPDI interface as well as a selection of PIC devices.  However since the protocol is compatible between all EDBG-based debuggers (pyedbglib) it is possible to use pymcuprog with a wide range of debuggers and devices, although not all device families/interfaces have been implemented.

### Debuggers / Tools
pymcuprog supports:
* PKOB nano (nEDBG) - on-board debugger on Curiosity Nano
* MPLAB PICkit 4 In-Circuit Debugger (when in 'AVR mode')
* MPLAB Snap In-Circuit Debugger (when in 'AVR mode')
* Atmel-ICE
* Power Debugger
* EDBG - on-board debugger on Xplained Pro/Ultra
* mEDBG - on-board debugger on Xplained Mini/Nano
* JTAGICE3 (firmware version 3.0 or newer)

Although not all functionality is provided on all debuggers/boards.  See device support section below.

### Devices
pymcuprog supports:
* All UPDI devices, whether mounted on kits or standalone
* PIC devices mounted on Curiosity Nano kits, or similar board with PKOB nano (nEDBG) debugger

Other devices (eg ATmega328P, ATsamd21e18a) may be partially supported for experimental purposes

##  Notes for Linux® systems
This package uses pyedbglib and other libraries for USB transport and some udev rules are required.  For details see the pyedbglib package: https://pypi.org/project/pyedbglib
