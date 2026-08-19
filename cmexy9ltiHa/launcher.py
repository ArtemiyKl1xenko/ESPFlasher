#!/usr/bin/env python3
"""
ESP Flasher Pro Edition - Setup & Auto-Update Manager
Установщик и автоматическое обновление приложения
"""

import os
import sys
import json
import subprocess
import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple
from urllib.request import urlopen
import tempfile
import zipfile


class UpdateManager:
    """Менеджер обновлений для ESP Flasher Pro."""

    REPO_URL = "https://api.github.com/repos/yourusername/esp-flasher-pro"
    CURRENT_VERSION = "5.0.0"
    UPDATE_CHECK_URL = f"{REPO_URL}/releases/latest"

    def __init__(self, app_dir: str = "."):
        self.app_dir = Path(app_dir)
        self.config_file = self.app_dir / "update_config.json"
        self.downloads_dir = self.app_dir / "downloads"
        self.backups_dir = self.app_dir / "backups"
        self.downloads_dir.mkdir(exist_ok=True)
        self.backups_dir.mkdir(exist_ok=True)

    def check_for_updates(self) -> Optional[dict]:
        """
        Проверить наличие новых версий.

        Returns:
            Словарь с информацией о новой версии или None
        """
        try:
            with urlopen(self.UPDATE_CHECK_URL, timeout=5) as response:
                data = json.loads(response.read().decode())
                latest_version = data.get('tag_name', '').lstrip('v')

                if self._compare_versions(latest_version, self.CURRENT_VERSION) > 0:
                    return {
                        'version': latest_version,
                        'url': data.get('zipball_url'),
                        'description': data.get('body', ''),
                        'released_at': data.get('published_at'),
                        'download_url': data.get('zipball_url')
                    }
        except Exception as e:
            print(f"[ERROR] Ошибка при проверке обновлений: {e}")

        return None

    def _compare_versions(self, version1: str, version2: str) -> int:
        """
        Сравнить две версии.

        Returns:
            1 если version1 > version2, -1 если <, 0 если равны
        """
        try:
            v1_parts = tuple(map(int, version1.split('.')))
            v2_parts = tuple(map(int, version2.split('.')))

            if v1_parts > v2_parts:
                return 1
            elif v1_parts < v2_parts:
                return -1
            else:
                return 0
        except:
            return 0

    def download_update(self, update_info: dict, progress_callback=None) -> Optional[str]:
        """
        Загрузить обновление.

        Returns:
            Путь к загруженному файлу или None
        """
        try:
            url = update_info['download_url']
            version = update_info['version']

            # Создаем имя файла для скачивания
            filename = f"esp-flasher-pro-v{version}.zip"
            filepath = self.downloads_dir / filename

            print(f"[*] Загрузка {filename}...")
            print(f"    URL: {url}")
            print(f"    Сохранить в: {filepath}")

            # Загрузим файл
            with urlopen(url, timeout=30) as response:
                total_size = int(response.headers.get('Content-Length', 0))
                downloaded = 0

                with open(filepath, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break

                        f.write(chunk)
                        downloaded += len(chunk)

                        if progress_callback and total_size:
                            progress = (downloaded / total_size) * 100
                            progress_callback(progress)
                        else:
                            print(f"    Загружено: {downloaded / 1024 / 1024:.2f} МБ")

            print(f"[✓] Загрузка завершена: {filepath}")
            return str(filepath)

        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке: {e}")
            return None

    def install_update(self, zip_path: str) -> bool:
        """
        Установить загруженное обновление.

        Returns:
            True если успешно, False иначе
        """
        try:
            print(f"[*] Установка обновления из {zip_path}...")

            # Сделаем резервную копию
            backup_path = self.backups_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"[*] Создание резервной копии в {backup_path}...")
            shutil.copytree(self.app_dir, backup_path, ignore=shutil.ignore_patterns('*.pyc', '__pycache__', 'downloads', '.git'))

            # Распакуем архив
            print(f"[*] Распаковка архива...")
            extract_dir = self.downloads_dir / "temp_extract"
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
            extract_dir.mkdir()

            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)

            # Найдем папку с исходным кодом (обычно 'username-repo-xxxxx')
            extracted_items = list(extract_dir.iterdir())
            if len(extracted_items) == 1 and extracted_items[0].is_dir():
                source_dir = extracted_items[0]
            else:
                source_dir = extract_dir

            # Копируем файлы
            print(f"[*] Копирование файлов...")
            for item in source_dir.iterdir():
                dest = self.app_dir / item.name

                if item.is_dir():
                    if dest.exists():
                        shutil.rmtree(dest)
                    shutil.copytree(item, dest)
                else:
                    shutil.copy2(item, dest)

            # Очистим временные файлы
            shutil.rmtree(extract_dir)

            print(f"[✓] Обновление установлено успешно!")
            return True

        except Exception as e:
            print(f"[ERROR] Ошибка при установке: {e}")
            print(f"[!] Восстановлением из резервной копии...")
            return False

    def get_installed_version(self) -> str:
        """Получить установленную версию."""
        return self.CURRENT_VERSION

    def save_update_config(self, config: dict):
        """Сохранить конфигурацию обновления."""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2, default=str)


class Launcher:
    """Лаунчер приложения с проверкой зависимостей."""

    def __init__(self):
        self.app_dir = Path(__file__).parent
        self.required_packages = [
            'esptool>=5.3.1',
            'pyserial>=3.5',
            'requests>=2.31.0',
            'pillow>=10.0.0'
        ]

    def check_python_version(self) -> bool:
        """Проверить версию Python."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 11):
            print(f"[ERROR] Требуется Python 3.11 или выше. Установлена версия {version.major}.{version.minor}")
            return False
        print(f"[✓] Python версия: {version.major}.{version.minor}")
        return True

    def check_dependencies(self) -> bool:
        """Проверить установленные зависимости."""
        print("[*] Проверка зависимостей...")

        missing_packages = []
        for package in self.required_packages:
            package_name = package.split('>=')[0]
            try:
                __import__(package_name)
                print(f"[✓] {package}")
            except ImportError:
                print(f"[✗] {package} - НЕ УСТАНОВЛЕН")
                missing_packages.append(package)

        if missing_packages:
            print(f"\n[!] Отсутствуют пакеты: {', '.join(missing_packages)}")
            print("[*] Установка недостающих пакетов...")

            try:
                subprocess.check_call([
                    sys.executable, '-m', 'pip', 'install', '-r',
                    'requirements.txt'
                ])
                print("[✓] Пакеты успешно установлены")
                return True
            except subprocess.CalledProcessError:
                print("[ERROR] Ошибка при установке пакетов")
                return False

        return True

    def run_app(self):
        """Запустить приложение."""
        try:
            # Проверяем версию Python
            if not self.check_python_version():
                return False

            # Проверяем зависимости
            if not self.check_dependencies():
                print("[!] Запуск с отсутствующими зависимостями...")

            # Проверяем обновления (опционально)
            print("\n[*] Проверка обновлений...")
            update_mgr = UpdateManager(self.app_dir)
            update_info = update_mgr.check_for_updates()

            if update_info:
                current_ver = update_mgr.get_installed_version()
                new_ver = update_info['version']
                print(f"[!] Доступно обновление: {current_ver} → {new_ver}")
                print(f"[!] Описание: {update_info['description'][:100]}...")

                choice = input("\n[?] Загрузить и установить обновление? (y/n): ").strip().lower()
                if choice == 'y':
                    zip_path = update_mgr.download_update(update_info)
                    if zip_path:
                        update_mgr.install_update(zip_path)
                        print("\n[!] Приложение будет перезапущено...")
                        os.execl(sys.executable, sys.executable, __file__)
            else:
                print("[✓] Приложение актуально")

            # Запустить главное приложение
            print("\n[*] Запуск ESP Flasher Pro Edition v5.0.0...")
            print("=" * 60)

            # Import and run the main app
            from cmexy9ltiHa.app_main import ESPFlasherProApp
            app = ESPFlasherProApp()
            app.mainloop()

            return True

        except Exception as e:
            print(f"[ERROR] Ошибка при запуске приложения: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Главная функция лаунчера."""
    print("╔" + "═" * 58 + "╗")
    print("║     ESP Flasher Pro Edition v5.0 - Launcher       ║")
    print("║  Максимально функциональное управление ESP32/ESP8266  ║")
    print("╚" + "═" * 58 + "╝")
    print()

    launcher = Launcher()
    success = launcher.run_app()

    if not success:
        sys.exit(1)


if __name__ == '__main__':
    main()
