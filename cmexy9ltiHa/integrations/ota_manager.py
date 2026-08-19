"""
OTA Manager - управление Over-The-Air обновлениями.
"""

import socket
import struct
from dataclasses import dataclass
from typing import Callable, Optional
from enum import Enum


class OTAStatus(Enum):
    """Статусы OTA процесса."""
    IDLE = "Неактивно"
    LISTENING = "Ожидание подключения"
    CONNECTED = "Подключено"
    TRANSFERRING = "Передача"
    COMPLETED = "Завершено"
    ERROR = "Ошибка"


@dataclass
class OTAConfig:
    """Конфигурация OTA."""
    listen_port: int = 3232  # Стандартный OTA порт
    listen_address: str = "0.0.0.0"
    timeout: float = 5.0
    chunk_size: int = 1024
    verify_checksum: bool = True
    require_auth: bool = False
    auth_password: str = ""


class OTAManager:
    """Менеджер OTA обновлений."""

    # OTA Protocol magic bytes
    OTA_MAGIC = b'\xe0'  # Первый байт OTA пакета

    def __init__(self, config: OTAConfig = None, on_status: Callable = None, on_progress: Callable = None):
        """
        Инициализация OTA менеджера.

        Args:
            config: Конфигурация OTA
            on_status: Callback для статуса
            on_progress: Callback для прогресса
        """
        self.config = config or OTAConfig()
        self.on_status = on_status or (lambda x: None)
        self.on_progress = on_progress or (lambda x: None)

        self.status = OTAStatus.IDLE
        self.server_socket = None
        self.client_socket = None

    def log_status(self, message: str):
        """Логировать статус."""
        self.on_status(message)

    def log_progress(self, progress: float, message: str = ""):
        """Логировать прогресс."""
        self.on_progress((progress, message))

    def start_listening(self) -> bool:
        """
        Начать уход за входящими OTA подключениями.

        Returns:
            True если успешно начато
        """
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.config.listen_address, self.config.listen_port))
            self.server_socket.listen(1)
            self.server_socket.settimeout(self.config.timeout)

            self.status = OTAStatus.LISTENING
            self.log_status(
                f"[✓ LISTENING] OTA режим ожидания на {self.config.listen_address}:{self.config.listen_port}\n"
            )

            return True

        except Exception as e:
            self.status = OTAStatus.ERROR
            self.log_status(f"[ERROR] {str(e)}\n")
            return False

    def stop_listening(self):
        """Остановить ожидание подключений."""
        try:
            if self.server_socket:
                self.server_socket.close()
            if self.client_socket:
                self.client_socket.close()

            self.status = OTAStatus.IDLE
            self.log_status("[INFO] OTA ожидание остановлено\n")

        except Exception as e:
            self.log_status(f"[ERROR] {str(e)}\n")

    def accept_connection(self) -> bool:
        """
        Ожидать подключения от ESP устройства.

        Returns:
            True если подключение получено
        """
        try:
            if not self.server_socket:
                return False

            self.client_socket, addr = self.server_socket.accept()

            self.status = OTAStatus.CONNECTED
            self.log_status(f"[✓ CONNECTED] Подключено с {addr[0]}:{addr[1]}\n")

            return True

        except socket.timeout:
            self.log_status("[WARNING] Timeout при ожидании подключения\n")
            return False
        except Exception as e:
            self.status = OTAStatus.ERROR
            self.log_status(f"[ERROR] {str(e)}\n")
            return False

    def send_firmware(self, firmware_path: str, chunk_size: int = None) -> bool:
        """
        Отправить firmware на подключенное устройство.

        Args:
            firmware_path: Путь к firmware файлу
            chunk_size: Размер куска передачи

        Returns:
            True если успешно отправлено
        """
        chunk_size = chunk_size or self.config.chunk_size

        try:
            if not self.client_socket:
                self.log_status("[ERROR] Нет подключения\n")
                return False

            # Читаем файл
            with open(firmware_path, 'rb') as f:
                firmware_data = f.read()

            file_size = len(firmware_data)
            self.log_status(f"[INFO] Отправка firmware ({file_size} байт)...\n")

            # Отправляем размер
            size_bytes = struct.pack('>I', file_size)
            self.client_socket.sendall(size_bytes)

            # Отправляем данные чанками
            self.status = OTAStatus.TRANSFERRING
            bytes_sent = 0

            while bytes_sent < file_size:
                chunk = firmware_data[bytes_sent:bytes_sent + chunk_size]
                self.client_socket.sendall(chunk)
                bytes_sent += len(chunk)

                progress = bytes_sent / file_size
                self.log_progress(progress, f"{bytes_sent}/{file_size} байт")

            self.status = OTAStatus.COMPLETED
            self.log_status("[✓ SUCCESS] Firmware успешно отправлена\n")

            return True

        except Exception as e:
            self.status = OTAStatus.ERROR
            self.log_status(f"[ERROR] {str(e)}\n")
            return False

    def receive_status(self) -> Optional[dict]:
        """
        Получить статус от устройства.

        Returns:
            Словарь со статусом или None
        """
        try:
            if not self.client_socket:
                return None

            # OTA статусы:
            # 0x01 = OK
            # 0x02 = Update Started
            # 0x03 = Update Progress
            # 0x04 = Update Finish
            # 0x05 = Update Failed

            data = self.client_socket.recv(1)

            if not data:
                return None

            status_code = data[0]
            status_map = {
                0x01: "OK",
                0x02: "Update Started",
                0x03: "Updating",
                0x04: "Completed",
                0x05: "Failed"
            }

            return {
                'code': status_code,
                'message': status_map.get(status_code, 'Unknown')
            }

        except Exception as e:
            self.log_status(f"[ERROR] {str(e)}\n")
            return None

    def get_device_info(self) -> Optional[dict]:
        """
        Получить информацию об устройстве (версия firmware, памяти и т.д.).

        Returns:
            Словарь с информацией или None
        """
        try:
            if not self.client_socket:
                return None

            # Запрашиваем информацию (команда 0xFF)
            self.client_socket.sendall(b'\xff')

            # Получаем ответ
            data = self.client_socket.recv(256)

            if data:
                return {
                    'raw_data': data.hex(),
                    'message': 'Информация получена'
                }

            return None

        except Exception as e:
            self.log_status(f"[ERROR] {str(e)}\n")
            return None

    def get_status_string(self) -> str:
        """Получить текстовое описание текущего статуса."""
        return self.status.value
