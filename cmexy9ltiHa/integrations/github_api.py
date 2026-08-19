"""
GitHub API - загрузка firmware из GitHub репозиториев.
"""

import json
import subprocess
from dataclasses import dataclass
from typing import List, Optional, Callable
from datetime import datetime
from pathlib import Path


@dataclass
class GitHubAsset:
    """Файл из GitHub Release."""
    name: str
    download_url: str
    size: int
    content_type: str


@dataclass
class GitHubRelease:
    """GitHub Release."""
    tag_name: str
    name: str
    description: str
    created_at: str
    assets: List[GitHubAsset]
    is_prerelease: bool = False
    is_latest: bool = False


class GitHubAPI:
    """API для работы с GitHub репозиториями."""

    BASE_URL = "https://api.github.com"

    def __init__(self, token: str = "", on_log: Callable = None):
        """
        Инициализация GitHub API.

        Args:
            token: GitHub API токен (опционально)
            on_log: Callback для логирования
        """
        self.token = token
        self.on_log = on_log or (lambda x: None)

    def log(self, message: str):
        """Добавить сообщение в лог."""
        self.on_log(message)

    def get_releases(self, owner: str, repo: str, include_prerelease: bool = False) -> List[GitHubRelease]:
        """
        Получить список releases репозитория.

        Args:
            owner: Владелец репозитория
            repo: Название репозитория
            include_prerelease: Включать ли prerelease версии

        Returns:
            Список GitHubRelease объектов
        """
        url = f"{self.BASE_URL}/repos/{owner}/{repo}/releases"

        try:
            cmd = ["curl", "-s", "-H", "Accept: application/vnd.github.v3+json"]

            if self.token:
                cmd.extend(["-H", f"Authorization: token {self.token}"])

            cmd.append(url)

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

            if result.returncode != 0:
                self.log(f"[ERROR] Ошибка при запросе к GitHub: {result.stderr}\n")
                return []

            releases_data = json.loads(result.stdout)
            releases = []

            for i, release_data in enumerate(releases_data):
                # Пропускаем prerelease если не нужны
                if release_data.get('prerelease', False) and not include_prerelease:
                    continue

                # Парсим assets
                assets = []
                for asset_data in release_data.get('assets', []):
                    if asset_data['name'].endswith('.bin'):  # Только .bin файлы
                        asset = GitHubAsset(
                            name=asset_data['name'],
                            download_url=asset_data['browser_download_url'],
                            size=asset_data.get('size', 0),
                            content_type=asset_data.get('content_type', '')
                        )
                        assets.append(asset)

                release = GitHubRelease(
                    tag_name=release_data['tag_name'],
                    name=release_data['name'],
                    description=release_data['body'][:500],  # Первые 500 символов
                    created_at=release_data['published_at'],
                    assets=assets,
                    is_prerelease=release_data.get('prerelease', False),
                    is_latest=(i == 0)  # Первый это latest
                )

                releases.append(release)
                self.log(f"[✓] Found release: {release.tag_name}\n")

            return releases

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return []

    def download_asset(self, asset: GitHubAsset, download_path: str, 
                      progress_callback: Callable = None) -> bool:
        """
        Загрузить файл из GitHub.

        Args:
            asset: GitHubAsset для загрузки
            download_path: Путь для сохранения
            progress_callback: Callback для прогресса загрузки

        Returns:
            True если успешно загружено
        """
        try:
            self.log(f"[INFO] Загрузка {asset.name}...\n")

            # Создаем папку если её нет
            Path(download_path).parent.mkdir(parents=True, exist_ok=True)

            cmd = ["curl", "-L", "-o", download_path, asset.download_url]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

            if result.returncode == 0:
                self.log(f"[✓] Успешно загружен: {asset.name}\n")
                return True
            else:
                self.log(f"[ERROR] Ошибка загрузки: {result.stderr}\n")
                return False

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return False

    def get_latest_release(self, owner: str, repo: str) -> Optional[GitHubRelease]:
        """
        Получить последний release репозитория.

        Args:
            owner: Владелец репозитория
            repo: Название репозитория

        Returns:
            GitHubRelease или None
        """
        releases = self.get_releases(owner, repo)
        return releases[0] if releases else None

    # Популярные репозитории ESP firmware
    POPULAR_REPOS = {
        'MicroPython-ESP32': ('micropython', 'micropython', 'releases'),
        'Tasmota': ('arendst', 'Tasmota', 'releases'),
        'ESPHome': ('esphome', 'esphome', 'releases'),
        'WLED': ('Aircoookie', 'WLED', 'releases'),
        'Arduino-ESP32': ('espressif', 'arduino-esp32', 'releases'),
    }

    def get_firmware_repository(self, repo_name: str) -> Optional[tuple]:
        """
        Получить информацию о популярном репозитории.

        Args:
            repo_name: Название репозитория

        Returns:
            Кортеж (owner, repo) или None
        """
        if repo_name in self.POPULAR_REPOS:
            owner, repo, _ = self.POPULAR_REPOS[repo_name]
            return (owner, repo)
        return None
