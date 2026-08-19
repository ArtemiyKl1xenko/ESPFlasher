"""
Advanced Monitor - продвинутый монитор последовательного порта.
"""

import threading
import tkinter as tk
from dataclasses import dataclass
from typing import Optional, Callable
from datetime import datetime

try:
    import serial
except ImportError:
    serial = None


@dataclass
class MonitorConfig:
    """Конфигурация монитора."""
    port: str
    baud_rate: int = 115200
    timeout: float = 1.0
    auto_start: bool = True
    buffer_size: int = 10000
    timestamp: bool = True
    colorize: bool = True


class AdvancedMonitor:
    """Продвинутый монитор последовательного порта с буферизацией и фильтрацией."""

    def __init__(self, config: MonitorConfig, on_data: Callable = None, on_error: Callable = None):
        """
        Инициализация монитора.

        Args:
            config: Конфигурация монитора
            on_data: Callback при получении данных
            on_error: Callback при ошибке
        """
        self.config = config
        self.on_data = on_data or (lambda x: None)
        self.on_error = on_error or (lambda x: None)

        self.serial = None
        self.is_running = False
        self.monitor_thread = None

        self.buffer = []
        self.line_buffer = ""

        self.filters = []  # Правила фильтрации

    def start(self) -> bool:
        """
        Начать мониторинг.

        Returns:
            True если успешно начато
        """
        if not serial:
            self.on_error("[ERROR] pyserial не установлен\n")
            return False

        try:
            self.serial = serial.Serial(
                port=self.config.port,
                baudrate=self.config.baud_rate,
                timeout=self.config.timeout
            )
            self.is_running = True

            self.monitor_thread = threading.Thread(target=self._read_loop, daemon=True)
            self.monitor_thread.start()

            self.on_data(f"[✓ STARTED] Монитор запущен на {self.config.port} @ {self.config.baud_rate} бод\n")
            return True

        except Exception as e:
            self.on_error(f"[ERROR] {str(e)}\n")
            return False

    def stop(self):
        """Остановить мониторинг."""
        self.is_running = False

        try:
            if self.serial and self.serial.is_open:
                self.serial.close()

            if self.monitor_thread:
                self.monitor_thread.join(timeout=5)

            self.on_data("[STOPPED] Мониторинг остановлен\n")

        except Exception as e:
            self.on_error(f"[ERROR] {str(e)}\n")

    def _read_loop(self):
        """Основной цикл чтения данных."""
        while self.is_running:
            try:
                if self.serial and self.serial.in_waiting:
                    data = self.serial.read(self.serial.in_waiting)
                    self._process_data(data)

            except Exception as e:
                if self.is_running:
                    self.on_error(f"[ERROR] {str(e)}\n")
                break

    def _process_data(self, data: bytes):
        """Обработать полученные данные."""
        try:
            # Декодируем данные
            text = data.decode('utf-8', errors='replace')

            # Обрабатываем символ за символом
            for char in text:
                if char == '\n':
                    # Полная строка получена
                    line = self.line_buffer.strip()
                    if line:
                        self._process_line(line)
                    self.line_buffer = ""
                else:
                    self.line_buffer += char

        except Exception as e:
            self.on_error(f"[ERROR] {str(e)}\n")

    def _process_line(self, line: str):
        """Обработать одну строку."""
        # Применяем фильтры
        if not self._match_filters(line):
            return

        # Добавляем timestamp если нужно
        if self.config.timestamp:
            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            line = f"[{timestamp}] {line}"

        # Добавляем в буфер
        self.buffer.append(line)
        if len(self.buffer) > self.config.buffer_size:
            self.buffer.pop(0)

        # Вызываем callback
        self.on_data(line + "\n")

    def _match_filters(self, line: str) -> bool:
        """Проверить соответствие фильтрам."""
        if not self.filters:
            return True

        for filter_rule in self.filters:
            if not filter_rule.match(line):
                return False

        return True

    def add_filter(self, pattern: str, inclusive: bool = True):
        """
        Добавить фильтр.

        Args:
            pattern: Текстовый паттерн
            inclusive: True если включить, False если исключить
        """
        self.filters.append(FilterRule(pattern, inclusive))

    def clear_filters(self):
        """Очистить фильтры."""
        self.filters.clear()

    def get_buffer(self) -> list:
        """Получить буфер данных."""
        return self.buffer.copy()

    def send_data(self, data: str) -> bool:
        """
        Отправить данные на устройство.

        Args:
            data: Данные для отправки

        Returns:
            True если успешно отправлено
        """
        if not self.serial or not self.serial.is_open:
            self.on_error("[ERROR] Порт не открыт\n")
            return False

        try:
            # Добавляем перевод строки если его нет
            if not data.endswith('\n'):
                data += '\n'

            self.serial.write(data.encode())
            return True

        except Exception as e:
            self.on_error(f"[ERROR] {str(e)}\n")
            return False


class FilterRule:
    """Правило фильтрации строк."""

    def __init__(self, pattern: str, inclusive: bool = True):
        """
        Инициализация правила.

        Args:
            pattern: Текстовый паттерн для поиска
            inclusive: True если строка ДОЛЖНА содержать паттерн
        """
        self.pattern = pattern
        self.inclusive = inclusive

    def match(self, text: str) -> bool:
        """
        Проверить соответствие правилу.

        Args:
            text: Текст для проверки

        Returns:
            True если соответствует
        """
        contains = self.pattern.lower() in text.lower()
        return contains if self.inclusive else not contains
