"""
Backup Manager - управление резервными копиями flash памяти.
"""

import os
import hashlib
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Callable
import json


@dataclass
class BackupInfo:
    """Информация о резервной копии."""
    name: str
    path: str
    device_port: str
    chip_name: str
    flash_size: str
    created_at: datetime
    file_size: int
    checksum: str = ""
    description: str = ""


class BackupManager:
    """Менеджер для резервного копирования flash памяти."""

    def __init__(self, backup_dir: str = "./backups", on_log: Callable = None):
        """
        Инициализация менеджера резервных копий.

        Args:
            backup_dir: Папка для хранения резервных копий
            on_log: Callback для логирования
        """
        self.backup_dir = backup_dir
        self.on_log = on_log or (lambda x: None)
        self.backups: List[BackupInfo] = []

        # Создаем папку если её нет
        Path(backup_dir).mkdir(parents=True, exist_ok=True)

        # Сканируем существующие резервные копии
        self.scan_backups()

    def log(self, message: str):
        """Добавить сообщение в лог."""
        self.on_log(message)

    def create_backup(self, backup_data: bytes, device_port: str, chip_name: str, 
                     flash_size: str = "4MB", description: str = "") -> bool:
        """
        Создать резервную копию.

        Args:
            backup_data: Данные flash памяти
            device_port: COM порт устройства
            chip_name: Имя чипа
            flash_size: Размер flash
            description: Описание резервной копии

        Returns:
            True если успешно создана
        """
        try:
            # Генерируем имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"backup_{chip_name}_{device_port.replace(':', '_')}_{timestamp}.bin"
            filepath = os.path.join(self.backup_dir, filename)

            # Сохраняем данные
            with open(filepath, 'wb') as f:
                f.write(backup_data)

            # Вычисляем checksum
            checksum = hashlib.sha256(backup_data).hexdigest()

            # Создаем информацию о резервной копии
            backup_info = BackupInfo(
                name=filename,
                path=filepath,
                device_port=device_port,
                chip_name=chip_name,
                flash_size=flash_size,
                created_at=datetime.now(),
                file_size=len(backup_data),
                checksum=checksum,
                description=description
            )

            self.backups.append(backup_info)
            self._save_metadata()

            self.log(f"[✓] Резервная копия создана: {filename}\n")
            return True

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return False

    def restore_backup(self, backup_name: str) -> Optional[bytes]:
        """
        Восстановить данные из резервной копии.

        Args:
            backup_name: Имя резервной копии

        Returns:
            Данные flash памяти или None
        """
        try:
            backup = None
            for b in self.backups:
                if b.name == backup_name:
                    backup = b
                    break

            if not backup:
                self.log(f"[ERROR] Резервная копия не найдена: {backup_name}\n")
                return None

            with open(backup.path, 'rb') as f:
                data = f.read()

            # Проверяем checksum
            checksum = hashlib.sha256(data).hexdigest()
            if checksum != backup.checksum:
                self.log("[WARNING] Checksum не совпадает! Данные могут быть повреждены\n")

            self.log(f"[✓] Резервная копия восстановлена: {backup_name}\n")
            return data

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return None

    def delete_backup(self, backup_name: str) -> bool:
        """
        Удалить резервную копию.

        Args:
            backup_name: Имя резервной копии

        Returns:
            True если успешно удалена
        """
        try:
            backup = None
            for b in self.backups:
                if b.name == backup_name:
                    backup = b
                    break

            if not backup:
                return False

            if os.path.exists(backup.path):
                os.remove(backup.path)

            self.backups.remove(backup)
            self._save_metadata()

            self.log(f"[✓] Резервная копия удалена: {backup_name}\n")
            return True

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return False

    def scan_backups(self):
        """Отсканировать папку и загрузить информацию о резервных копиях."""
        self.backups.clear()

        try:
            for file in Path(self.backup_dir).glob("*.bin"):
                backup_info = BackupInfo(
                    name=file.name,
                    path=str(file),
                    device_port="unknown",
                    chip_name="unknown",
                    flash_size="unknown",
                    created_at=datetime.fromtimestamp(file.stat().st_mtime),
                    file_size=file.stat().st_size
                )
                self.backups.append(backup_info)

            self.log(f"[✓] Найдено резервных копий: {len(self.backups)}\n")

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")

    def get_all_backups(self) -> List[BackupInfo]:
        """Получить все резервные копии."""
        return self.backups.copy()

    def get_backup_info(self, backup_name: str) -> Optional[BackupInfo]:
        """Получить информацию о резервной копии."""
        for backup in self.backups:
            if backup.name == backup_name:
                return backup
        return None

    def _save_metadata(self):
        """Сохранить метаданные резервных копий."""
        try:
            metadata_file = os.path.join(self.backup_dir, ".metadata.json")

            data = {
                'backups': [
                    {
                        'name': b.name,
                        'device_port': b.device_port,
                        'chip_name': b.chip_name,
                        'flash_size': b.flash_size,
                        'created_at': b.created_at.isoformat(),
                        'file_size': b.file_size,
                        'checksum': b.checksum,
                        'description': b.description
                    }
                    for b in self.backups
                ]
            }

            with open(metadata_file, 'w') as f:
                json.dump(data, f, indent=2)

        except Exception as e:
            self.log(f"[WARNING] Не удалось сохранить метаданные: {e}\n")

    def get_total_backup_size(self) -> int:
        """Получить общий размер всех резервных копий в байтах."""
        return sum(b.file_size for b in self.backups)
