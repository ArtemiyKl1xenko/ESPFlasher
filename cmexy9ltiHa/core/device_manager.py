"""
Device Manager - управление ESP32/ESP8266 устройствами.
Отвечает за обнаружение, подключение, получение информации о чипе.
"""

import subprocess
import sys
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime

try:
    import serial
    import serial.tools.list_ports
except ImportError:
    serial = None


@dataclass
class DeviceInfo:
    """Информация об ESP устройстве."""
    port: str
    chip_name: str
    chip_id: str
    mac_address: str = ""
    crystal_freq: str = "40M"
    flash_size: str = "4MB"
    flash_mode: str = "dio"
    flash_freq: str = "80M"
    sdk_version: str = "unknown"
    connected_at: datetime = None

    def to_dict(self):
        return {
            'port': self.port,
            'chip_name': self.chip_name,
            'chip_id': self.chip_id,
            'mac_address': self.mac_address,
            'crystal_freq': self.crystal_freq,
            'flash_size': self.flash_size,
            'flash_mode': self.flash_mode,
            'flash_freq': self.flash_freq,
            'sdk_version': self.sdk_version,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None
        }


class DeviceManager:
    """Менеджер для всех операций с ESP устройствами."""

    def __init__(self, on_log: callable = None):
        """
        Инициализация менеджера устройств.

        Args:
            on_log: Функция для логирования. Signature: on_log(message: str)
        """
        self.on_log = on_log or (lambda x: None)
        self.connected_devices: Dict[str, DeviceInfo] = {}
        self.current_device: Optional[DeviceInfo] = None

    def log(self, message: str):
        """Добавить сообщение в лог."""
        self.on_log(message)

    def list_available_ports(self) -> List[str]:
        """
        Получить список доступных COM портов.

        Returns:
            Список портов (например: ['COM3', 'COM5'])
        """
        if not serial:
            self.log("[ERROR] pyserial не установлен\n")
            return []

        ports = []
        try:
            for port, desc, hwid in serial.tools.list_ports.comports():
                ports.append(port)
                self.log(f"Found: {port} - {desc}\n")
        except Exception as e:
            self.log(f"[ERROR] Ошибка при сканировании портов: {e}\n")

        return ports

    def detect_device(self, port: str, baud: int = 115200) -> Optional[DeviceInfo]:
        """
        Обнаружить подключенное ESP устройство.

        Args:
            port: COM порт
            baud: Скорость передачи

        Returns:
            DeviceInfo если устройство найдено, иначе None
        """
        cmd = [sys.executable, "-m", "esptool", "--port", port, "--baud", str(baud), "chip_id"]
        self.log(f"> {' '.join(cmd)}\n")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=15
            )
            output, _ = process.communicate()
            self.log(output)

            # Парсим результат
            device_info = self._parse_chip_info(output, port)
            if device_info:
                device_info.connected_at = datetime.now()
                self.connected_devices[port] = device_info
                self.current_device = device_info
                self.log(f"\n[✓ SUCCESS] Обнаружено: {device_info.chip_name}\n")
                return device_info
            else:
                self.log("[✗ ERROR] Не удалось определить тип чипа\n")
                return None

        except subprocess.TimeoutExpired:
            self.log("[ERROR] Timeout при обнаружении чипа\n")
            return None
        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return None

    def _parse_chip_info(self, output: str, port: str) -> Optional[DeviceInfo]:
        """Парсить информацию о чипе из esptool output."""
        try:
            chip_name = "Unknown"
            chip_id = "Unknown"
            mac_address = ""

            # Парсим chip name
            for line in output.split('\n'):
                if 'Chip is' in line:
                    parts = line.split('Chip is')
                    if len(parts) > 1:
                        chip_str = parts[1].strip().split('(')[0].strip()
                        chip_name = chip_str

                if 'Chip ID:' in line:
                    chip_id = line.split('Chip ID:')[1].strip()

                if 'MAC:' in line or 'MAC address' in line:
                    mac_parts = line.split()
                    for i, part in enumerate(mac_parts):
                        if part == 'MAC' and i + 1 < len(mac_parts):
                            mac_address = mac_parts[i + 1]

            return DeviceInfo(
                port=port,
                chip_name=chip_name,
                chip_id=chip_id,
                mac_address=mac_address
            )
        except Exception as e:
            self.log(f"[ERROR] Ошибка парсинга: {e}\n")
            return None

    def get_device_info(self, port: str) -> Optional[DeviceInfo]:
        """Получить информацию о подключенном устройстве."""
        if port in self.connected_devices:
            return self.connected_devices[port]
        return self.detect_device(port)

    def read_flash(self, port: str, output_path: str, size: str = "4MB", 
                   baud: int = 115200, progress_callback: callable = None) -> bool:
        """
        Прочитать flash память устройства (резервная копия).

        Args:
            port: COM порт
            output_path: Путь для сохранения файла
            size: Размер flash памяти (например: '4MB', '16MB')
            baud: Скорость передачи
            progress_callback: Callback для прогресса

        Returns:
            True если успешно, False иначе
        """
        cmd = [
            sys.executable, "-m", "esptool",
            "--port", port,
            "--baud", str(baud),
            "read_flash", "0", size, output_path
        ]

        self.log(f"> {' '.join(cmd)}\n")
        self.log(f"[INFO] Чтение flash памяти {size} из {port}...\n")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            for line in iter(process.stdout.readline, ''):
                self.log(line)
                if progress_callback:
                    progress_callback(line)

            return_code = process.wait()
            if return_code == 0:
                self.log(f"[✓ SUCCESS] Flash успешно сохранена в {output_path}\n")
                return True
            else:
                self.log(f"[ERROR] Чтение flash завершилось с кодом {return_code}\n")
                return False

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return False

    def erase_device(self, port: str, baud: int = 115200) -> bool:
        """
        Полностью стереть flash память устройства.

        Args:
            port: COM порт
            baud: Скорость передачи

        Returns:
            True если успешно, False иначе
        """
        cmd = [
            sys.executable, "-m", "esptool",
            "--port", port,
            "--baud", str(baud),
            "erase_flash"
        ]

        self.log(f"> {' '.join(cmd)}\n")
        self.log("[WARNING] Стирание всей flash памяти...\n")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            for line in iter(process.stdout.readline, ''):
                self.log(line)

            return_code = process.wait()
            if return_code == 0:
                self.log("[✓ SUCCESS] Flash память полностью стирана\n")
                return True
            else:
                self.log(f"[ERROR] Стирание завершилось с кодом {return_code}\n")
                return False

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return False
