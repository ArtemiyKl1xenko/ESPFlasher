"""
Analytics - сбор анализов статистики использования приложения.
"""

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Callable
from enum import Enum


class EventType(Enum):
    """Типы событий."""
    APP_START = "app_start"
    APP_CLOSE = "app_close"
    FLASH_START = "flash_start"
    FLASH_SUCCESS = "flash_success"
    FLASH_FAILED = "flash_failed"
    DEVICE_DETECTED = "device_detected"
    DEVICE_FAILED = "device_failed"
    MONITOR_START = "monitor_start"
    MONITOR_STOP = "monitor_stop"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    OTA_START = "ota_start"
    OTA_SUCCESS = "ota_success"
    OTA_FAILED = "ota_failed"
    FEATURE_USED = "feature_used"


@dataclass
class AnalyticsEvent:
    """Событие аналитики."""
    event_type: EventType
    timestamp: datetime
    duration_seconds: float = 0.0
    details: Dict = None
    success: bool = True
    error_message: str = ""

    def __post_init__(self):
        if self.details is None:
            self.details = {}


class Analytics:
    """Сбор и анализ статистики использования."""

    def __init__(self, data_dir: str = "./data", enable: bool = True, on_log: Callable = None):
        """
        Инициализация аналитики.

        Args:
            data_dir: Папка для хранения данных аналитики
            enable: Включена ли аналитика
            on_log: Callback для логирования
        """
        self.data_dir = data_dir
        self.enable = enable
        self.on_log = on_log or (lambda x: None)
        self.events: List[AnalyticsEvent] = []

        # Создаем папку если её нет
        Path(data_dir).mkdir(parents=True, exist_ok=True)

        # Загружаем предыдущие события
        self.load_events()

    def log(self, message: str):
        """Логировать сообщение."""
        self.on_log(message)

    def track_event(self, event: AnalyticsEvent) -> bool:
        """
        Отследить событие.

        Args:
            event: Событие аналитики

        Returns:
            True если успешно записано
        """
        if not self.enable:
            return False

        try:
            self.events.append(event)
            self.save_events()
            return True

        except Exception as e:
            self.log(f"[WARNING] Ошибка при сохранении события: {e}\n")
            return False

    def save_events(self):
        """Сохранить события в файл."""
        try:
            events_file = os.path.join(self.data_dir, "analytics.json")

            events_data = []
            for event in self.events:
                events_data.append({
                    'event_type': event.event_type.value,
                    'timestamp': event.timestamp.isoformat(),
                    'duration_seconds': event.duration_seconds,
                    'details': event.details,
                    'success': event.success,
                    'error_message': event.error_message
                })

            with open(events_file, 'w') as f:
                json.dump(events_data, f, indent=2)

        except Exception as e:
            self.log(f"[WARNING] {str(e)}\n")

    def load_events(self):
        """Загрузить события из файла."""
        try:
            events_file = os.path.join(self.data_dir, "analytics.json")

            if not os.path.exists(events_file):
                return

            with open(events_file, 'r') as f:
                events_data = json.load(f)

            self.events.clear()
            for event_data in events_data:
                event = AnalyticsEvent(
                    event_type=EventType(event_data['event_type']),
                    timestamp=datetime.fromisoformat(event_data['timestamp']),
                    duration_seconds=event_data.get('duration_seconds', 0.0),
                    details=event_data.get('details', {}),
                    success=event_data.get('success', True),
                    error_message=event_data.get('error_message', '')
                )
                self.events.append(event)

        except Exception as e:
            self.log(f"[WARNING] {str(e)}\n")

    def get_statistics(self) -> Dict:
        """
        Получить статистику использования.

        Returns:
            Словарь со статистикой
        """
        stats = {
            'total_events': len(self.events),
            'events_by_type': {},
            'success_rate': 0.0,
            'total_flash_time': 0.0,
            'total_devices_flashed': 0,
            'most_used_features': []
        }

        # Группируем события по типам
        for event in self.events:
            event_type = event.event_type.value
            if event_type not in stats['events_by_type']:
                stats['events_by_type'][event_type] = 0
            stats['events_by_type'][event_type] += 1

        # Рассчитываем success rate
        successful = sum(1 for e in self.events if e.success)
        if len(self.events) > 0:
            stats['success_rate'] = (successful / len(self.events)) * 100

        # Суммируем время флешинга
        flash_events = [e for e in self.events if 'flash' in e.event_type.value]
        stats['total_flash_time'] = sum(e.duration_seconds for e in flash_events)

        return stats

    def get_events_by_type(self, event_type: EventType) -> List[AnalyticsEvent]:
        """Получить события определенного типа."""
        return [e for e in self.events if e.event_type == event_type]

    def get_failed_events(self) -> List[AnalyticsEvent]:
        """Получить неудачные события."""
        return [e for e in self.events if not e.success]

    def clear_events(self) -> bool:
        """Очистить все события."""
        try:
            self.events.clear()
            self.save_events()
            return True
        except Exception:
            return False

    def export_report(self, filepath: str) -> bool:
        """
        Экспортировать отчет в HTML.

        Args:
            filepath: Путь для сохранения отчета

        Returns:
            True если успешно экспортировано
        """
        try:
            stats = self.get_statistics()

            html_content = f"""
            <html>
            <head>
                <title>ESP Flasher Analytics Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    h1 {{ color: #0078d4; }}
                    table {{ border-collapse: collapse; width: 100%; margin-top: 20px; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                    th {{ background-color: #0078d4; color: white; }}
                </style>
            </head>
            <body>
                <h1>ESP Flasher Analytics Report</h1>
                <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

                <h2>Statistics</h2>
                <table>
                    <tr><th>Metric</th><th>Value</th></tr>
                    <tr><td>Total Events</td><td>{stats['total_events']}</td></tr>
                    <tr><td>Success Rate</td><td>{stats['success_rate']:.1f}%</td></tr>
                    <tr><td>Total Flash Time</td><td>{stats['total_flash_time']:.1f}s</td></tr>
                </table>

                <h2>Events by Type</h2>
                <table>
                    <tr><th>Event Type</th><th>Count</th></tr>
                    {''.join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in stats['events_by_type'].items())}
                </table>
            </body>
            </html>
            """

            with open(filepath, 'w') as f:
                f.write(html_content)

            self.log(f"[✓] Отчет экспортирован: {filepath}\n")
            return True

        except Exception as e:
            self.log(f"[ERROR] {str(e)}\n")
            return False
