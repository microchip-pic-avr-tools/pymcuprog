"""
Generate drag-and-drop configuration files for PIC devices through device support scripts

The generated device blob can be used to provide drag and drop programming support for kits with
onboard debuggers
"""
# Python 3 compatibility for Python 2
from __future__ import print_function

# args, logging
import argparse
import logging
import os
import sys

from pymcuprog.deviceinfo.configgenerator import ConfigGenerator

def main(args, loglevel):
    """
    Main program
    """
    logging.basicConfig(format="%(levelname)s: %(message)s", level=loglevel)

    # Enforce XML output
    if args.filename:
        if os.path.splitext(args.filename)[1] != '.xml':
            print ("Target filename (-f) must be of type .xml")
            sys.exit(-1)

    generator = ConfigGenerator()

    generator.load_device_model(args.device, args.packpath)
    generator.process_programming_functions()
    contents = generator.get_xml_string()
    if args.filename:
        print("Writing to file '{0:s}'".format(args.filename))
        with open(args.filename, "w") as xmlfile:
            xmlfile.write(contents)
    else:
        print("Config generator output:")
        print(contents)
    print("Done")

PARSER = argparse.ArgumentParser(description="Config generator")

# Device to program
PARSER.add_argument("device",
                    help="device to use")

# Pack path
PARSER.add_argument("-p", "--packpath",
                    type=str,
                    help="path to pack")

PARSER.add_argument("-f", "--filename",
                    type=str,
                    help="file to write")

PARSER.add_argument("-v", "--verbose",
                    help="verbose output",
                    action="store_true")

ARGUMENTS = PARSER.parse_args()

# Setup logging
if ARGUMENTS.verbose:
    LOGGING_LEVEL = logging.INFO
else:
    LOGGING_LEVEL = logging.WARNING

main(ARGUMENTS, LOGGING_LEVEL)
