"""
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
"""

import sys
from pyftdi.i2c import I2cController

class I2cShim:
    def __init__(self, ftdi_url='ftdi://ftdi:232h/1'):
        self.i2c = I2cController()
        self.i2c.configure(ftdi_url)
        self.slaves = {}
    
    def get_port(self, address):
        if address not in self.slaves:
            self.slaves[address] = self.i2c.get_port(address)
        return self.slaves[address]
    
    # SMBus interface methods
    def read_byte_data(self, address, register):
        port = self.get_port(address)
        return port.read_from(register, 1)[0]
    
    def write_byte_data(self, address, register, value):
        port = self.get_port(address)
        port.write_to(register, [value])
    
    def read_i2c_block_data(self, address, register, length):
        port = self.get_port(address)
        return list(port.read_from(register, length))
    
    def write_i2c_block_data(self, address, register, data):
        port = self.get_port(address)
        port.write_to(register, data)
    
    def write_byte(self, address, value):
        port = self.get_port(address)
        port.write([value])
    
    def read_byte(self, address):
        port = self.get_port(address)
        return port.read(1)[0]

class MockSMBus:
    def __init__(self, bus_number=1):
        self.shim = I2cShim()
    
    def __getattr__(self, name):
        return getattr(self.shim, name)

class MockBusIO:
    def __init__(self):
        self.i2c_controller = I2cController()
        self.i2c_controller.configure('ftdi://ftdi:232h/1')
    
    def I2C(self, scl=None, sda=None, frequency=100000):
        return MockI2CDevice(self.i2c_controller)

class MockI2CDevice:
    def __init__(self, controller):
        self.controller = controller
        self.slaves = {}
    
    def writeto(self, address, buffer):
        if address not in self.slaves:
            self.slaves[address] = self.controller.get_port(address)
        self.slaves[address].write(buffer)
    
    def readfrom_into(self, address, buffer):
        if address not in self.slaves:
            self.slaves[address] = self.controller.get_port(address)
        data = self.slaves[address].read(len(buffer))
        for i, byte in enumerate(data):
            buffer[i] = byte

# Mock qwiic_i2c driver that uses pyftdi
class MockQwiicI2C:
    def __init__(self, *args, **kwargs):
        self.shim = I2cShim()
        
    def isDeviceConnected(self, address):
        """Check if device is connected by attempting to read from it"""
        try:
            port = self.shim.get_port(address)
            # Try to read one byte - if it fails, device not connected
            port.read(1)
            return True
        except:
            return False
    
    def is_device_connected(self, address):
        return self.isDeviceConnected(address)
    
    def ping(self, address):
        return self.isDeviceConnected(address)
        
    def readByte(self, address, register):
        return self.shim.read_byte_data(address, register)
    
    def read_byte(self, address, register):
        return self.readByte(address, register)
        
    def writeByte(self, address, register, value):
        self.shim.write_byte_data(address, register, value)
        
    def write_byte(self, address, register, value):
        self.writeByte(address, register, value)
        
    def readBlock(self, address, register, length):
        return self.shim.read_i2c_block_data(address, register, length)
        
    def read_block(self, address, register, length):
        return self.readBlock(address, register, length)
        
    def writeBlock(self, address, register, data):
        self.shim.write_i2c_block_data(address, register, data)
        
    def write_block(self, address, register, data):
        self.writeBlock(address, register, data)
    
    def readWord(self, address, register):
        data = self.shim.read_i2c_block_data(address, register, 2)
        return data[0] | (data[1] << 8)
    
    def read_word(self, address, register):
        return self.readWord(address, register)
        
    def writeWord(self, address, register, value):
        data = [value & 0xFF, (value >> 8) & 0xFF]
        self.shim.write_i2c_block_data(address, register, data)
        
    def write_word(self, address, register, value):
        self.writeWord(address, register, value)
    
    def scan(self):
        """Scan for I2C devices"""
        found = []
        for addr in range(0x08, 0x78):  # Standard I2C address range
            if self.isDeviceConnected(addr):
                found.append(addr)
        return found

# Automatically patch common I2C modules when this shim is imported
def patch_i2c_modules():
    # Patch smbus
    mock_smbus = type('MockSMBusModule', (), {'SMBus': MockSMBus})()
    sys.modules['smbus'] = mock_smbus
    sys.modules['smbus2'] = mock_smbus
    
    # Patch busio for CircuitPython/Adafruit libraries
    sys.modules['busio'] = MockBusIO()
    
    # Patch board module (often used with busio)
    mock_board = type('MockBoard', (), {
        'SCL': 'mock_scl',
        'SDA': 'mock_sda'
    })()
    sys.modules['board'] = mock_board
    
    # Patch qwiic_i2c module - this is the key addition for SparkFun libraries
    mock_qwiic_i2c = type('MockQwiicI2CModule', (), {
        'getI2CDriver': lambda *args, **kwargs: MockQwiicI2C(*args, **kwargs),
        'get_i2c_driver': lambda *args, **kwargs: MockQwiicI2C(*args, **kwargs)
    })()
    sys.modules['qwiic_i2c'] = mock_qwiic_i2c

# Auto-patch when imported
patch_i2c_modules()

print("I2C shim loaded - Raspberry Pi I2C libraries will now use pyftdi")