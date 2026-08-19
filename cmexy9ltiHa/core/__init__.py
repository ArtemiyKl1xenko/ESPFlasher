"""
Core module - основные компоненты ESP Flasher Pro Edition.
"""

from .device_manager import DeviceManager, DeviceInfo
from .firmware_manager import FirmwareManager, FirmwareInfo
from .settings_manager import SettingsManager

__all__ = [
    'DeviceManager',
    'DeviceInfo',
    'FirmwareManager',
    'FirmwareInfo',
    'SettingsManager'
]

__version__ = '5.0.0'
