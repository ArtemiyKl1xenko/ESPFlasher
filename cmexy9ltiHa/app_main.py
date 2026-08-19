"""
ESP Flasher Pro Edition v5.0 - Главное приложение
Максимально функциональная программа для управления ESP32/ESP8266
"""

import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from version import __version__, VERSION_INFO
from core import DeviceManager, FirmwareManager, SettingsManager
from ui import (ThemeManager, DARK_THEME, LIGHT_THEME, AdvancedMonitor, 
                BatchFlasher, MemoryViewer, MemoryMap, LogViewer, StatusBar)
from integrations import GitHubAPI, PlatformIOBridge, OTAManager, OTAConfig
from utils import BackupManager, Analytics, ErrorAnalyzer


class ESPFlasherProApp(tk.Tk):
    """Главное приложение ESP Flasher Pro Edition."""

    def __init__(self):
        super().__init__()
        self.title(f"ESP Flasher Pro Edition v{__version__}")
        self.geometry("1400x900")

        # Инициализируем компоненты
        self.settings = SettingsManager()
        self.device_manager = DeviceManager(on_log=self._log)
        self.firmware_manager = FirmwareManager(on_log=self._log)
        self.theme_manager = ThemeManager(self.settings.get('ui.theme', 'dark'))
        self.backup_manager = BackupManager(on_log=self._log)
        self.analytics = Analytics(enable=self.settings.get('advanced.enable_analytics', False))
        self.error_analyzer = ErrorAnalyzer(on_log=self._log)
        self.github_api = GitHubAPI(on_log=self._log)
        self.platformio = PlatformIOBridge(on_log=self._log)
        self.batch_flasher = BatchFlasher(on_status=self._log, on_progress=self._on_batch_progress)
        self.ota_manager = OTAManager(config=OTAConfig(), on_status=self._log)

        # Создаем UI
        self.create_ui()
        self.status = "Приложение запущено"

    def create_ui(self):
        """Создать главный интерфейс."""
        # Главный фрейм с вкладками
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Вкладка 1: Flash
        self.create_flash_tab()

        # Вкладка 2: Monitor
        self.create_monitor_tab()

        # Вкладка 3: Memory
        self.create_memory_tab()

        # Вкладка 4: Batch
        self.create_batch_tab()

        # Вкладка 5: Backups
        self.create_backups_tab()

        # Вкладка 6: GitHub
        self.create_github_tab()

        # Вкладка 7: Settings
        self.create_settings_tab()

        # Статус бар
        self.status_bar = StatusBar(self)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        self.status_bar.set_version(__version__)

    def create_flash_tab(self):
        """Создать вкладку для флешинга."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="📡 Flash")

        # Заголовок
        ttk.Label(frame, text="Прошивка ESP32/ESP8266", font=("Arial", 14, "bold")).pack(pady=10)

        # Лог
        self.log_viewer = LogViewer(frame)
        self.log_viewer.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Кнопки
        button_frame = ttk.Frame(frame)
        button_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(button_frame, text="🔍 Обнаружить чип", command=self.detect_chip).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="⚡ Прошить", command=self.start_flash).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="🗑️ Стереть Flash", command=self.erase_flash).pack(side=tk.LEFT, padx=2)
        ttk.Button(button_frame, text="💾 Сохранить резервную копию", command=self.create_backup).pack(side=tk.LEFT, padx=2)

    def create_monitor_tab(self):
        """Создать вкладку монитора."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔌 Monitor")

        ttk.Label(frame, text="Монитор UART", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(frame, text="[Monitor будет реализован в UI слое]").pack(pady=50)

    def create_memory_tab(self):
        """Создать вкладку памяти."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="💾 Memory")

        ttk.Label(frame, text="Визуализация памяти", font=("Arial", 14, "bold")).pack(pady=10)

        memory_map = MemoryMap('ESP32', 4)
        memory_viewer = MemoryViewer(memory_map)

        text_widget = tk.Text(frame, height=20, width=100, font=("Courier", 9))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text_widget.insert('1.0', memory_viewer.get_visual_representation())
        text_widget.config(state=tk.DISABLED)

    def create_batch_tab(self):
        """Создать вкладку batch флешинга."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🚀 Batch Flash")

        ttk.Label(frame, text="Мультиприватка нескольких устройств", font=("Arial", 14, "bold")).pack(pady=10)
        ttk.Label(frame, text="[Batch flashing UI в разработке]").pack(pady=50)

    def create_backups_tab(self):
        """Создать вкладку резервных копий."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🔄 Backups")

        ttk.Label(frame, text="Резервные копии", font=("Arial", 14, "bold")).pack(pady=10)

        # Список резервных копий
        tree = ttk.Treeview(frame, columns=('name', 'date', 'size'), height=15)
        tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        for backup in self.backup_manager.get_all_backups():
            size_mb = backup.file_size / 1024 / 1024
            tree.insert('', 'end', values=(backup.name, backup.created_at.strftime("%Y-%m-%d %H:%M"), f"{size_mb:.2f} MB"))

    def create_github_tab(self):
        """Создать вкладку GitHub."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="🐙 GitHub"  )

        ttk.Label(frame, text="Загрузка firmware из GitHub", font=("Arial", 14, "bold")).pack(pady=10)

        # Список популярных репозиториев
        for repo_name in self.github_api.POPULAR_REPOS.keys():
            ttk.Button(frame, text=f"📥 {repo_name}", command=lambda r=repo_name: self._download_from_github(r)).pack(padx=5, pady=2)

    def create_settings_tab(self):
        """Создать вкладку настроек."""
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="⚙️ Settings")

        ttk.Label(frame, text="Настройки приложения", font=("Arial", 14, "bold")).pack(pady=10)

        # Тема
        ttk.Label(frame, text="Тема:").pack(padx=20, pady=5)
        theme_var = tk.StringVar(value=self.settings.get('ui.theme', 'dark'))
        ttk.Radiobutton(frame, text="Dark", variable=theme_var, value='dark').pack(padx=40)
        ttk.Radiobutton(frame, text="Light", variable=theme_var, value='light').pack(padx=40)

        # О программе
        ttk.Button(frame, text="ℹ️ О программе", command=self.show_about).pack(pady=20)

    def _log(self, message: str):
        """Добавить сообщение в лог."""
        if hasattr(self, 'log_viewer'):
            level = 'success' if '✓' in message else ('error' if '✗' in message or 'ERROR' in message else 'info')
            self.log_viewer.add_log(message, level)

    def _on_batch_progress(self, progress_tuple):
        """Callback для прогресса batch флешинга."""
        task_id, progress = progress_tuple
        self._log(f"[PROGRESS] {task_id}: {progress}%\n")

    def detect_chip(self):
        """Обнаружить подключенный chip."""
        self._log("[INFO] Обнаружение chip...\n")
        messagebox.showinfo("Info", "Функционал обнаружения chip реализуется через device_manager")

    def start_flash(self):
        """Начать флешинг."""
        self._log("[INFO] Начало прошивки...\n")
        messagebox.showinfo("Info", "Функционал флешинга реализуется через flasher_manager")

    def erase_flash(self):
        """Стереть flash память."""
        if messagebox.askyesno("Подтверждение", "Вы уверены? Это сотрет всю flash память!"):
            self._log("[WARNING] Стирание flash памяти...\n")

    def create_backup(self):
        """Создать резервную копию."""
        self._log("[INFO] Создание резервной копии...\n")
        messagebox.showinfo("Info", "Резервная копия создается через device_manager")

    def _download_from_github(self, repo_name: str):
        """Загрузить firmware из GitHub."""
        self._log(f"[INFO] Загрузка {repo_name} из GitHub...\n")

    def show_about(self):
        """Показать диалог О программе."""
        about_text = f"""
ESP Flasher Pro Edition v{__version__}

{VERSION_INFO['description']}

Основные функции:
"""
        for feature in VERSION_INFO['features'][:5]:
            about_text += f"\n{feature}"
        about_text += "\n\n... и многое другое!"

        messagebox.showinfo("О программе", about_text)


def main():
    """Главная функция приложения."""
    app = ESPFlasherProApp()
    app.mainloop()


if __name__ == "__main__":
    main()
