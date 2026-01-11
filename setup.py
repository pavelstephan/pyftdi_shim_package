
# creates python library package for shim so that it can be called from anywhere
from setuptools import setup

setup(
    name='pyftdi-shim',
    version='1.0.0',
    description='I2C Shim for using Raspberry Pi I2C libraries with pyftdi on Mac/PC',
    py_modules=['pyftdi_shim'],
    python_requires='>=3.6',
    install_requires=[
        'pyftdi',
    ],
)