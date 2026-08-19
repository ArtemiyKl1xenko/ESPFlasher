"""
Settings Manager - управление конфигурацией и настройками приложения.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime


class SettingsManager:
    """Менеджер для хранения и управления настройками приложения."""

    DEFAULT_SETTINGS = {
        'ui': {
            'theme': 'dark',  # dark, light, auto
            'window_width': 1200,
            'window_height': 700,
            'remember_window_size': True,
            'show_help_on_startup': False,
            'font_size': 10,
            'monospace_font': 'Courier New'
        },
        'flash': {
            'default_baud_rate': 460800,
            'default_flash_freq': '80m',
            'default_flash_mode': 'dio',
            'auto_detect': True,
            'verify_after_write': True,
            'erase_before_write': False
        },
        'monitor': {
            'baud_rate': 115200,
            'auto_scroll': True,
            'buffer_size': 10000,  # строк
            'timestamp': True,
            'filter_enabled': False,
            'filter_text': ''
        },
        'advanced': {
            'enable_batch_flashing': True,
            'thread_pool_size': 4,
            'enable_backups': True,
            'backup_dir': './backups',
            'enable_analytics': False,
            'enable_updates': True
        },
        'github': {
            'api_token': '',  # будет зашифрован
            'auto_download_latest': False,
            'cache_firmware': True,
            'cache_dir': './firmware_cache'
        }
    }

    def __init__(self, config_dir: str = "./config"):
        """
        Инициализация менеджера настроек.

        Args:
            config_dir: Папка для хранения конфигураций
        """
        self.config_dir = config_dir
        self.config_file = os.path.join(config_dir, 'settings.json')
        self.settings = self.DEFAULT_SETTINGS.copy()

        # Создаем папку если её нет
        Path(config_dir).mkdir(parents=True, exist_ok=True)

        # Загружаем сохраненные настройки
        self.load()

    def load(self) -> bool:
        """
        Загрузить настройки из файла.

        Returns:
            True если успешно загружено, False если ошибка или файл не существует
        """
        if not os.path.exists(self.config_file):
            self.save()  # Создаем файл с настройками по умолчанию
            return False

        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                saved_settings = json.load(f)

            # Мергируем с defaults (для новых опций)
            self.settings = self._deep_merge(self.DEFAULT_SETTINGS.copy(), saved_settings)
            return True

        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке настроек: {e}")
            return False

    def save(self) -> bool:
        """
        Сохранить текущие настройки в файл.

        Returns:
            True если успешно сохранено
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            return True

        except Exception as e:
            print(f"[ERROR] Ошибка при сохранении настроек: {e}")
            return False

    def get(self, key_path: str, default: Any = None) -> Any:
        """
        Получить значение настройки по пути.

        Args:
            key_path: Путь вида 'section.key' или просто 'key'
            default: Значение по умолчанию

        Returns:
            Значение настройки

        Example:
            value = settings.get('ui.theme')
            baud = settings.get('flash.default_baud_rate')
        """
        keys = key_path.split('.')
        value = self.settings

        try:
            for key in keys:
                value = value[key]
            return value

        except (KeyError, TypeError):
            return default

    def set(self, key_path: str, value: Any) -> bool:
        """
        Установить значение настройки по пути.

        Args:
            key_path: Путь вида 'section.key'
            value: Новое значение

        Returns:
            True если успешно установлено

        Example:
            settings.set('ui.theme', 'light')
        """
        keys = key_path.split('.')

        try:
            current = self.settings

            # Переходим к нужной секции
            for key in keys[:-1]:
                if key not in current:
                    current[key] = {}
                current = current[key]

            # Устанавливаем значение
            current[keys[-1]] = value
            return True

        except Exception as e:
            print(f"[ERROR] Ошибка при установке настройки: {e}")
            return False

    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Получить всю секцию настроек.

        Args:
            section: Название секции (например: 'ui', 'flash')

        Returns:
            Словарь с настройками секции
        """
        return self.settings.get(section, {})

    def set_section(self, section: str, values: Dict[str, Any]) -> bool:
        """
        Установить всю секцию настроек.

        Args:
            section: Название секции
            values: Словарь с новыми значениями

        Returns:
            True если успешно установлено
        """
        try:
            if section not in self.settings:
                self.settings[section] = {}

            self.settings[section].update(values)
            return True

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return False

    def reset_to_defaults(self) -> bool:
        """
        Сбросить все настройки на значения по умолчанию.

        Returns:
            True если успешно сброшено
        """
        try:
            self.settings = self.DEFAULT_SETTINGS.copy()
            self.save()
            return True

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return False

    def export_settings(self, file_path: str) -> bool:
        """
        Экспортировать настройки в файл.

        Args:
            file_path: Путь для сохранения

        Returns:
            True если успешно экспортировано
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=2, ensure_ascii=False)
            print(f"[✓] Настройки экспортированы в {file_path}")
            return True

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return False

    def import_settings(self, file_path: str) -> bool:
        """
        Импортировать настройки из файла.

        Args:
            file_path: Путь к файлу с настройками

        Returns:
            True если успешно импортировано
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported = json.load(f)

            self.settings = self._deep_merge(self.DEFAULT_SETTINGS.copy(), imported)
            self.save()
            print(f"[✓] Настройки импортированы из {file_path}")
            return True

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return False

    @staticmethod
    def _deep_merge(base: Dict, updates: Dict) -> Dict:
        """
        Рекурсивно мергировать два словаря.

        Args:
            base: Базовый словарь
            updates: Словарь с обновлениями

        Returns:
            Мергированный словарь
        """
        result = base.copy()

        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = SettingsManager._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def to_dict(self) -> Dict:
        """Получить все настройки как словарь."""
        return self.settings.copy()

    def from_dict(self, data: Dict) -> bool:
        """
        Загрузить настройки из словаря.

        Args:
            data: Словарь с настройками

        Returns:
            True если успешно загружено
        """
        try:
            self.settings = self._deep_merge(self.DEFAULT_SETTINGS.copy(), data)
            return True

        except Exception as e:
            print(f"[ERROR] {str(e)}")
            return False
