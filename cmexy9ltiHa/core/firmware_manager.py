"""
Firmware Manager - управление firmware файлами и их загрузкой.
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict
from pathlib import Path


@dataclass
class FirmwareInfo:
    """Информация о firmware файле."""
    name: str
    path: str
    size: int
    address: str = "0x1000"
    version: str = "unknown"
    description: str = ""
    tags: List[str] = None
    date_added: datetime = None
    chip_compatible: List[str] = None

    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.chip_compatible is None:
            self.chip_compatible = ["all"]
        if self.date_added is None:
            self.date_added = datetime.now()

    def to_dict(self):
        return {
            'name': self.name,
            'path': self.path,
            'size': self.size,
            'address': self.address,
            'version': self.version,
            'description': self.description,
            'tags': self.tags,
            'date_added': self.date_added.isoformat() if self.date_added else None,
            'chip_compatible': self.chip_compatible
        }


class FirmwareManager:
    """Менеджер для управления firmware файлами."""

    # Встроенные предустановки
    PRESETS = {
        'ESP32-Arduino': {
            'name': 'Arduino для ESP32',
            'version': '2.x',
            'address': '0x1000',
            'description': 'Стандартная Arduino среда для ESP32',
            'url': 'https://raw.githubusercontent.com/espressif/arduino-esp32/master/tools/sdk/bin/'
        },
        'MicroPython-ESP32': {
            'name': 'MicroPython для ESP32',
            'version': '1.20.x',
            'address': '0x1000',
            'description': 'MicroPython интерпретатор для ESP32',
            'url': 'https://micropython.org/download/esp32/'
        },
        'Tasmota-ESP32': {
            'name': 'Tasmota для ESP32',
            'version': '13.x',
            'address': '0x1000',
            'description': 'Tasmota IoT прошивка (всё в одном файле)',
            'url': 'https://github.com/arendst/Tasmota/releases'
        },
        'WLED-ESP32': {
            'name': 'WLED для ESP32',
            'version': '0.14.x',
            'address': '0x1000',
            'description': 'WLED контроллер для LED полос',
            'url': 'https://github.com/Aircoookie/WLED/releases'
        },
        'ESPHome-ESP32': {
            'name': 'ESPHome для ESP32',
            'version': '2023.x',
            'address': '0x1000',
            'description': 'ESPHome framework для интеграции с Home Assistant',
            'url': 'https://esphome.io/index.html'
        }
    }

    def __init__(self, firmware_dir: str = "./firmware", on_log: callable = None):
        """
        Инициализация менеджера firmware.

        Args:
            firmware_dir: Папка для хранения firmware файлов
            on_log: Callback для логирования
        """
        self.firmware_dir = firmware_dir
        self.on_log = on_log or (lambda x: None)
        self.firmware_cache: Dict[str, FirmwareInfo] = {}

        # Создаем папку если её нет
        Path(firmware_dir).mkdir(parents=True, exist_ok=True)

    def log(self, message: str):
        """Добавить сообщение в лог."""
        self.on_log(message)

    def scan_firmware_directory(self) -> List[FirmwareInfo]:
        """
        Сканировать папку с firmware файлами.

        Returns:
            Список FirmwareInfo объектов
        """
        self.firmware_cache.clear()
        firmware_list = []

        try:
            for file_path in Path(self.firmware_dir).glob('*.bin'):
                size = os.path.getsize(file_path)
                firmware_info = FirmwareInfo(
                    name=file_path.stem,
                    path=str(file_path),
                    size=size
                )
                self.firmware_cache[file_path.stem] = firmware_info
                firmware_list.append(firmware_info)
                self.log(f"[INFO] Найден firmware: {file_path.name} ({self._format_size(size)})\n")

        except Exception as e:
            self.log(f"[ERROR] Ошибка при сканировании папки: {e}\n")

        return firmware_list

    def get_preset(self, preset_name: str) -> Optional[Dict]:
        """
        Получить информацию о встроенной предустановке.

        Args:
            preset_name: Название предустановки

        Returns:
            Словарь с информацией о предустановке
        """
        return self.PRESETS.get(preset_name)

    def get_all_presets(self) -> Dict[str, Dict]:
        """Получить все встроенные предустановки."""
        return self.PRESETS.copy()

    def add_firmware(self, firmware_info: FirmwareInfo) -> bool:
        """
        Добавить новую информацию о firmware в кэш.

        Args:
            firmware_info: Информация о firmware

        Returns:
            True если успешно добавлено
        """
        try:
            if not os.path.exists(firmware_info.path):
                self.log(f"[WARNING] Файл не найден: {firmware_info.path}\n")
                return False

            self.firmware_cache[firmware_info.name] = firmware_info
            self.log(f"[INFO] Firmware добавлен: {firmware_info.name}\n")
            return True

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return False

    def get_firmware(self, name: str) -> Optional[FirmwareInfo]:
        """Получить информацию о firmware по имени."""
        return self.firmware_cache.get(name)

    def get_all_firmware(self) -> List[FirmwareInfo]:
        """Получить все загруженные firmware."""
        return list(self.firmware_cache.values())

    def remove_firmware(self, name: str) -> bool:
        """
        Удалить firmware из кэша и удалить файл если требуется.

        Args:
            name: Имя firmware

        Returns:
            True если успешно удалено
        """
        if name not in self.firmware_cache:
            return False

        firmware = self.firmware_cache[name]

        try:
            if os.path.exists(firmware.path):
                os.remove(firmware.path)
                self.log(f"[INFO] Файл удален: {firmware.path}\n")

            del self.firmware_cache[name]
            return True

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return False

    def get_firmware_info_from_file(self, file_path: str) -> Optional[FirmwareInfo]:
        """
        Получить информацию о firmware из файла.

        Args:
            file_path: Путь к файлу

        Returns:
            FirmwareInfo если файл существует
        """
        try:
            if not os.path.exists(file_path):
                return None

            size = os.path.getsize(file_path)
            name = Path(file_path).stem

            return FirmwareInfo(
                name=name,
                path=file_path,
                size=size
            )

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return None

    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Форматировать размер в читаемый вид."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"

    def validate_firmware(self, file_path: str) -> bool:
        """
        Валидировать firmware файл (базовая проверка).

        Args:
            file_path: Путь к файлу

        Returns:
            True если файл выглядит как валидный firmware
        """
        try:
            if not os.path.exists(file_path):
                self.log(f"[ERROR] Файл не найден: {file_path}\n")
                return False

            with open(file_path, 'rb') as f:
                magic = f.read(1)
                # ESP firmware обычно начинается с 0xE9
                if magic == b'\xe9':
                    self.log(f"[✓] Файл выглядит как валидный ESP firmware\n")
                    return True
                else:
                    self.log(f"[WARNING] Файл может быть не ESP firmware (magic: {magic.hex()})\n")
                    return False

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return False
