"""
pymcuprog
Tools for programming of MCUs using Microchip CMSIS-DAP based debuggers
"""
from os import path
from os import chdir
from os import popen
import sys
import time
# To use a consistent encoding
from codecs import open
from setuptools import setup
if sys.version_info < (3,3):
    from setuptools import find_packages
else:
    from setuptools import find_namespace_packages

here = path.abspath(path.dirname(__file__))
chdir(here)

# Get the long description from the pypi file
# Using UTF8 and single newlines
with open(path.join(here, 'pypi.md'), 'rb') as f:
    long_description = f.read().decode("utf-8").replace('\r\n', '\n')

# Set the package name:
name = 'pymcuprog'

"""
Package version :
The version number follow the format major.minor.patch.build
major, minor and patch are set manually according to semantic versioning 2.0.0: https://semver.org
build is an incrementing number set by a build server
in case of installing from source, a Local Version Identifier (see PEP 440) is added
"""

# Package version setup
PACKAGE_VERSION = {
    "major": 3,
    "minor": 14,
    "patch": 2,
    # Will be replaced by build number from Jenkins. For local builds the build number is 0 and the 'snapshot' is
    # added as Local Version Identifier
    "build": '9',
}

version = "{}.{}.{}.{}".format(PACKAGE_VERSION['major'], PACKAGE_VERSION['minor'],
                               PACKAGE_VERSION['patch'], PACKAGE_VERSION['build'])
print("Building {} version: {}".format(name, version))

# Create a "version.py" file in the package
fname = "{}/version.py".format(name)
with open(path.join(here, fname), 'w') as f:
    f.write("\"\"\" This file was generated when {} was built \"\"\"\n".format(name))
    f.write("VERSION = '{}'\n".format(version))
    # The command below can fail if git command not available, or not in a git workspace folder
    result = popen("git rev-parse HEAD").read()
    commit_id = result.splitlines()[0] if result else "N/A"
    f.write("COMMIT_ID = '{}'\n".format(commit_id))
    f.write("BUILD_DATE = '{}'\n".format(time.strftime("%Y-%m-%d %H:%M:%S %z")))

# Read in requirements (dependencies) file
with open('requirements.txt') as f:
    install_requires = f.read()

if sys.version_info < (3,3):
    packages=find_packages(exclude=['tests'])
else:
    packages=find_namespace_packages(exclude=['tests'])


setup(
    name=name,
    version=version,
    description='Tools for programming of MCUs using Microchip CMSIS-DAP based debuggers',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/microchip-pic-avr-tools/pymcuprog',
    license='MIT',
    author='Microchip Technology',
    author_email='support@microchip.com',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Embedded Systems',
        'License :: OSI Approved :: MIT License',
        # pymcuprog does also work on Python 2.7 but it is not officially supported
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: Microsoft :: Windows',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS',
    ],
    packages=packages,

    # List of packages required to use this package
    install_requires=install_requires,

    # List of packages required to develop and test this package
    extras_require={
        'dev': ['pylint', 'mock', 'parameterized', 'pytest'],
    },

    # Include files from MANIFEST.in
    include_package_data=True,

    # Installable CLI entry point
    entry_points={
        'console_scripts': [
            'pymcuprog=pymcuprog.pymcuprog:main',
        ],
    },
)
