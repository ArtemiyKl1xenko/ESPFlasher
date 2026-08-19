"""
ESP Flasher Pro Edition v5.0
Максимально функциональная программа для управления ESP32/ESP8266
"""

__title__ = "ESP Flasher Pro Edition"
__version__ = "5.0.0"
__release__ = "Pro Edition"
__description__ = "Уникальная программа для прошивки и управления ESP32/ESP8266 устройств"
__author__ = "ESP Flasher Team"
__license__ = "MIT"

__all__ = [
    '__title__',
    '__version__',
    '__release__',
    '__description__',
    '__author__',
    '__license__'
]

# Version info для About диалога
VERSION_INFO = {
    'version': __version__,
    'release': __release__,
    'description': __description__,
    'features': [
        '✓ Поддержка всех ESP32 вариантов (ESP32, S2, S3, C3, C6, H2)',
        '✓ Поддержка ESP8266',
        '✓ Мультиприватка (до 4 устройств одновременно)',
        '✓ Продвинутый монитор последовательного порта',
        '✓ Визуализация памяти и partition таблицы',
        '✓ Резервное копирование flash памяти',
        '✓ Встроенные предустановки (Arduino, MicroPython, Tasmota, WLED, ESPHome)',
        '✓ Dark/Light темы',
        '✓ Интеграция с GitHub (загрузка firmware)',
        '✓ Поддержка OTA обновлений',
        '✓ Интеграция с PlatformIO',
        '✓ Полная история операций',
        '✓ Профили конфигураций',
        '✓ Горячие клавиши',
    ],
    'requirements': [
        'Python 3.11+',
        'pyserial 3.5+',
        'esptool 5.3.1+',
    ],
    'changelog': {
        '5.0.0': [
            'Полная переработка архитектуры приложения',
            'Добавлен Core Layer (device_manager, firmware_manager, settings)',
            'Добавлен UI Layer (advanced_monitor, batch_flasher, memory_viewer)',
            'Добавлен Integration Layer (GitHub API, PlatformIO, OTA)',
            'Поддержка Dark/Light тем',
            'Мультиприватка',
            'Резервное копирование flash',
        ]
    }
}
