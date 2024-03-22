# Changelog


## [3.17] - March 2024

### Added
- DSG-7091 Add CLI command to convert hex file to UF2

### Changed
- DSG-6630 Improve presentation of memory data on console

### Fixed
- DSG-6636 UPDI devices tinyAVR(R)/megaAVR(R) overwrites preceding bytes when writing single values to user row
- DSG-7110 Programming failure of AVR64DU32 target with pymcuprog
- DSG-7223 Serial UPDI uses Flash page buffer erase for EEPROM on AVR EA and EB
- DSG-7224 Serial UPDI does not support writing complete user row in one operation for AVR DU

## [3.16] - November 2023

### Added
- DSG-6057 Added support for BOOT_ROW memtype
- DSG-6631 Added serialupdi support for P:4 and P:5
- DSG-6213 Added AVR EB

### Changed
- DSG-5887 Refactor serialupdi NVM variants
- DSG-6210 Made serialupdi logging more concise
- DSG-6533 Help tweaks

### Fixed
- DSG-5817 Improved error handling with SAM devices
- DSG-6409 Error return code when --verify fails
- DSG-6590 Corrected AVR Ex to use 24-bit addressing for serialupdi

## [3.14] - October 2022

### Added
- DSG-5158 github-28 Added CLI switch for serial port read timeout
- DSG-5421 Added support for AVR DU and additional AVR DD devices

### Changed
- DSG-5418 Added Python 3.10 metadata tag
- DSG-5543 Removed Python 3.6 metadata tag
- DSG-5417 Removed distutils usage

### Fixed
- DSG-5157 github-29 Fixed return value on error
- DSG-4836 Corrected flash offset compensation for avrdebugger

## [3.13] - May 2022

### Added
- DSG-3936 Fixed AVR ISP implementation and added commands (beta)
- DSG-4172 github-10 Disable ACK response signature on serialUPDI block write (speed-up)
- DSG-3951 github-8 Added --erase argument to erase device before write with single execution
- DSG-3972 CLI help additions
- DSG-3997 Added debugwire_disable() to Avr8Protocol

### Fixed
- DSG-3945, DSG-3938 Unable to write fuse byte 0 on Curiosity Nano ATtiny kits
- DSG-4488 github-19 Return bytearray (not list) from serialUPDI read
- DSG-4594 SAMD21 performance improvement (SAM-IoT provisioning)
- DSG-4540 Fixed SAMD21 non-word-oriented read failure
- DSG-3941 Improved feedback on verification failure
- DSG-3944 Removed timeout warning for serialUPDI with a locked device
- DSG-4419 Corrected AVR high voltage UPDI device data
- DSG-3993 github-9 Corrected AVR signature sizes to make additional data available

## [3.10] - October 2021

### Added
- DSG-2702 Add serialupdi backend for AVR EA
- DSG-3633 github-3 Add missing AVR-DB devices
- DSG-3635 github-4 Add missing ATtiny devices
- DSG-3662 Add ascii-art for serialUPDI
- DSG-3804 Add py39 metadata to package
- DSG-3943 github-7 Add CLI documentation

### Fixed
- DSG-2859 github-1 serialUPDI write user_row on locked device fails
- DSG-3538 github-2 Unable to write fuses on ATmega4809 using serialUPDI
- DSG-3817 SAM D21 user row programming fails
- DSG-3952 Incorrect size of FUSES on Dx, Ex devices

## [3.9] - April 2021

### Added
- DSG-2920 Raise exception if device ID does not match
- DSG-2918 SerialUPDI: error recovery if non-ascii characters are read in SIB
- DSG-2861 Valid memory types are listed if an invalid one is specified

### Fixed
- DSG-3238 PIC16 eeprom displays incorrect address
- DSG-3239 PIC16 eeprom verification does not work
- DSG-2925 UPDI device revision not correctly parsed/displayed
- DSG-2860 SerialUPDI: chip erase does not work on locked device
- DSG-2857 SerialUPDI: crash when writing lockbits
- DSG-2855 Verify action fails if hex file contains eeprom content
- DSG-2854 User row excluded when reading to hex file
- DSG-2850 UPDI device model fix (sram)

### Changed
- DSG-2862 Improved exception handling
- DSG-3203 Improved exception handling
- DSG-3178 Cosmetic changes for publication

## [3.7.4] - December 2020

### Added
- DSG-1492 Added verify function
- DSG-2039 Added all UPDI devices
- DSG-2279 Added error codes
- DSG-1550 Flash-only erase

### Fixed
- DSG-2470 No feedback when multiple kits are connected
- DSG-2014 Error when reading using -m and -o but no -b
- DSG-2738 Padding to page size when writing user row on locked device

### Changed
- DSG-2234 Logging using logging module
- DSG-2034 prevent read using -b with no -m specified
- DSG-2009 prevent writing from hexfile with memory type specified
- DSG-2012 prevent writing from hexfile with offset specified
- DSG-2458 documentation changes
- DSG-2041 documentation changes
- DSG-2042 documentation changes
- DSG-2043 documentation changes
- DSG-2011 documentation changes

## [3.1.3] - June 2020
- First public release to PyPi
