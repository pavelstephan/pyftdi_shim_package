I2C Shim for using Raspberry Pi I2C libraries with pyftdi on Mac/PC
Simply import this module before importing any RPi I2C libraries.

To use, add the following to code:

import pyftdi_shim  # Must be BEFORE any other I2C imports
from as7343 import AS7343  # Now this will use pyftdi instead of RPi I2C

AND, in init method, change the below from:

# self.i2c = smbus.SMBus(1)
# self.sensor = AS7343(self.i2c)

To:

import smbus  # This will now be your pyftdi-backed mock
self.i2c = smbus.SMBus(1)  # The "1" is ignored, uses pyftdi
self.sensor = AS7343(self.i2c)


To run, create this file structure and put these files in the appropriate folder:

pyftdi_shim_package/
├── pyftdi_shim.egg-info/                    
│   ├── PKG-INFO/
│   ├── dependency_links.txt/
│   └── ... other 3 text files at this same level 
│--setup.py
|--pyftdi_shim.py

