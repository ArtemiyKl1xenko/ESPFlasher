"""
PlatformIO Bridge - интеграция с PlatformIO IDE/CLI.
"""

import subprocess
import os
import json
from dataclasses import dataclass
from typing import List, Optional, Dict, Callable
from pathlib import Path


@dataclass
class PIOBoard:
    """PlatformIO плата."""
    id: str
    name: str
    platform: str
    frameworks: List[str]
    upload_protocol: str
    build_flags: str = ""


@dataclass
class PIOProject:
    """PlatformIO проект."""
    name: str
    path: str
    platform: str
    board: str
    framework: str
    version: str = "unknown"


class PlatformIOBridge:
    """Интеграция с PlatformIO."""

    def __init__(self, on_log: Callable = None):
        """
        Инициализация PlatformIO моста.

        Args:
            on_log: Callback для логирования
        """
        self.on_log = on_log or (lambda x: None)
        self.pio_installed = self._check_pio_installed()

    def log(self, message: str):
        """Добавить сообщение в лог."""
        self.on_log(message)

    def _check_pio_installed(self) -> bool:
        """Проверить установлен ли PlatformIO."""
        try:
            result = subprocess.run(
                ["platformio", "--version"],
                capture_output=True,
                text=True,
                timeout=5
            )
            is_installed = result.returncode == 0
            if is_installed:
                self.log(f"[✓] PlatformIO найден: {result.stdout.strip()}\n")
            else:
                self.log("[INFO] PlatformIO не установлен\n")
            return is_installed
        except Exception:
            self.log("[INFO] PlatformIO не установлен\n")
            return False

    def get_boards(self, platform: str = "espressif32") -> List[PIOBoard]:
        """
        Получить список доступных плат.

        Args:
            platform: Платформа (espressif32, espressif8266)

        Returns:
            Список PIOBoard объектов
        """
        if not self.pio_installed:
            self.log("[WARNING] PlatformIO не установлен\n")
            return []

        try:
            cmd = ["platformio", "boards", platform, "--json-output"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)

            if result.returncode != 0:
                self.log(f"[ERROR] Ошибка при получении списка плат\n")
                return []

            boards_data = json.loads(result.stdout)
            boards = []

            for board_id, board_info in boards_data.items():
                board = PIOBoard(
                    id=board_id,
                    name=board_info.get('name', ''),
                    platform=platform,
                    frameworks=board_info.get('frameworks', []),
                    upload_protocol=board_info.get('upload', {}).get('protocol', 'serial')
                )
                boards.append(board)

            self.log(f"[✓] Найдено плат: {len(boards)}\n")
            return boards

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return []

    def build_project(self, project_path: str) -> bool:
        """
        Собрать PlatformIO проект.

        Args:
            project_path: Путь к проекту

        Returns:
            True если успешно собрано
        """
        if not self.pio_installed:
            self.log("[ERROR] PlatformIO не установлен\n")
            return False

        try:
            self.log(f"[INFO] Сборка проекта: {project_path}...\n")

            cmd = ["platformio", "run", "-d", project_path]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            self.log(result.stdout)

            if result.returncode == 0:
                self.log("[✓] Проект успешно собран\n")
                return True
            else:
                self.log(f"[ERROR] Сборка профессионала: {result.stderr}\n")
                return False

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return False

    def upload_firmware(self, project_path: str, port: str = None) -> bool:
        """
        Загрузить firmware на устройство через PlatformIO.

        Args:
            project_path: Путь к проекту
            port: COM порт (опционально)

        Returns:
            True если успешно загружено
        """
        if not self.pio_installed:
            self.log("[ERROR] PlatformIO не установлен\n")
            return False

        try:
            self.log(f"[INFO] Загрузка firmware на {port}...\n")

            cmd = ["platformio", "run", "-d", project_path, "-t", "upload"]

            if port:
                cmd.extend(["--upload-port", port])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            self.log(result.stdout)

            if result.returncode == 0:
                self.log("[✓] Firmware успешно загружена\n")
                return True
            else:
                self.log(f"[ERROR] Загрузка ошибка: {result.stderr}\n")
                return False

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return False

    def get_project_info(self, project_path: str) -> Optional[PIOProject]:
        """
        Получить информацию о PlatformIO проекте.

        Args:
            project_path: Путь к проекту

        Returns:
            PIOProject или None
        """
        try:
            config_file = os.path.join(project_path, "platformio.ini")

            if not os.path.exists(config_file):
                self.log("[ERROR] platformio.ini не найден\n")
                return None

            # Простой парсер для .ini файла
            config = {}
            with open(config_file, 'r') as f:
                current_section = None
                for line in f:
                    line = line.strip()
                    if line.startswith('[') and line.endswith(']'):
                        current_section = line[1:-1]
                        config[current_section] = {}
                    elif '=' in line and current_section:
                        key, value = line.split('=', 1)
                        config[current_section][key.strip()] = value.strip()

            # Ищем [env:...]
            env_config = None
            for section in config.keys():
                if section.startswith('env:'):
                    env_config = config[section]
                    break

            if not env_config:
                return None

            project = PIOProject(
                name=os.path.basename(project_path),
                path=project_path,
                platform=env_config.get('platform', ''),
                board=env_config.get('board', ''),
                framework=env_config.get('framework', '')
            )

            self.log(f"[✓] Project: {project.name} ({project.platform})\n")
            return project

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return None
