"""
Error Analyzer - анализ и диагностика ошибок флешинга.
"""

import re
from dataclasses import dataclass
from typing import List, Optional, Dict, Callable
from enum import Enum


class ErrorSeverity(Enum):
    """Уровень серьезности ошибки."""
    INFO = "Info"
    WARNING = "Warning"
    ERROR = "Error"
    CRITICAL = "Critical"


@dataclass
class ErrorReport:
    """Отчет об ошибке."""
    error_code: str
    message: str
    severity: ErrorSeverity
    likely_causes: List[str]
    suggested_solutions: List[str]
    raw_error: str = ""


class ErrorAnalyzer:
    """Анализ и диагностика ошибок."""

    # Известные ошибки и их решения
    ERROR_DATABASE = {
        'FAILED_CONNECT': {
            'severity': ErrorSeverity.CRITICAL,
            'message': 'Не удалось подключиться к устройству',
            'causes': [
                'USB кабель не подключен',
                'Неправильный COM порт выбран',
                'Драйверы USB не установлены',
                'Устройство не в режиме загрузки (нужно нажать кнопку BOOT и перезагрузить)'
            ],
            'solutions': [
                'Проверьте USB кабель',
                'Перезагрузите устройство (конопка RST)',
                'Нажмите кнопку BOOT, затем RST, чтобы войти в режим загрузки',
                'Переустановите драйверы usb (esp-idf-tools или CH340)',
                'Попробуйте другой USB кабель'
            ]
        },
        'INVALID_MAGIC': {
            'severity': ErrorSeverity.ERROR,
            'message': 'Неверный отклик от устройства',
            'causes': [
                'Файл firmware повреждена',
                'Неверная скорость передачи (baud rate)',
                'Устройство не ESP32/ESP8266'
            ],
            'solutions': [
                'Проверьте целостность firmware файла',
                'Попробуйте меньшую скорость передачи (например 115200)',
                'Убедитесь что подключено нужное устройство'
            ]
        },
        'TIMEOUT': {
            'severity': ErrorSeverity.ERROR,
            'message': 'Timeout при выполнении операции',
            'causes': [
                'Свадение USB нестабильно',
                'Устройство зависло',
                'Слишком выс окая скорость передачи'
            ],
            'solutions': [
                'Переподключите USB кабель',
                'Перезагрузите устройство',
                'Уменьшите скорость передачи',
                'Попробуйте другой USB порт'
            ]
        },
        'VERIFICATION_FAILED': {
            'severity': ErrorSeverity.WARNING,
            'message': 'Проверка целостности данных не прошла',
            'causes': [
                'Данные повреждены во время передачи',
                'EMI/помехи'
            ],
            'solutions': [
                'Попробуйте еще раз',
                'Отключите другие USB устройства',
                'Используйте качественный USB кабель',
                'Убедитесь что отключена опция verify (если вам не нужна проверка)'
            ]
        },
        'WRITE_FAILED': {
            'severity': ErrorSeverity.ERROR,
            'message': 'Ошибка при записи в flash',
            'causes': [
                'Flash память повреждена',
                'Попытка записи в защищенную область',
                'Недостаточно памяти'
            ],
            'solutions': [
                'Попробуйте выполнить полное стирание flash (erase_flash)',
                'Убедитесь что адрес и размер верны',
                'Используйте меньший файл firmware',
                'Свяжитесь с производителем если проблема сохраняется'
            ]
        },
        'CHIP_ID_MISMATCH': {
            'severity': ErrorSeverity.ERROR,
            'message': 'Тип чипа не совпадает с firmware',
            'causes': [
                'Firmware предназначена для другого чипа',
                'Неверное обнаружение чипа'
            ],
            'solutions': [
                'Убедитесь что используете firmware для вашего чипа',
                'Использование правильный файл для ESP32/ESP8266',
                'Попробуйте выполнить выявления чипа заново'
            ]
        }
    }

    def __init__(self, on_log: Callable = None):
        """
        Инициализация анализатора ошибок.

        Args:
            on_log: Callback для логирования
        """
        self.on_log = on_log or (lambda x: None)

    def log(self, message: str):
        """Логировать сообщение."""
        self.on_log(message)

    def analyze_error(self, error_output: str) -> Optional[ErrorReport]:
        """
        Анализировать выходные данные об ошибке.

        Args:
            error_output: Текст ошибки от esptool

        Returns:
            ErrorReport или None если ошибка не распознана
        """
        error_output = error_output.lower()

        # Ищем известные ошибки
        for error_code, error_info in self.ERROR_DATABASE.items():
            # Ищем ключевые слова
            if any(keyword in error_output for keyword in self._get_keywords(error_code)):
                return ErrorReport(
                    error_code=error_code,
                    message=error_info['message'],
                    severity=error_info['severity'],
                    likely_causes=error_info['causes'],
                    suggested_solutions=error_info['solutions'],
                    raw_error=error_output
                )

        # Если не найдена известная ошибка, ищем имерны
        return self._analyze_generic_error(error_output)

    def _get_keywords(self, error_code: str) -> List[str]:
        """Получить ключевые слова для распознавания ошибки."""
        keywords_map = {
            'FAILED_CONNECT': ['connect', 'failed to connect', 'unable', 'timeout', 'no response'],
            'INVALID_MAGIC': ['invalid magic', 'bad magic'],
            'TIMEOUT': ['timeout', 'timed out'],
            'VERIFICATION_FAILED': ['verification', 'crc', 'checksum', 'failed'],
            'WRITE_FAILED': ['write', 'failed'],
            'CHIP_ID_MISMATCH': ['chip id', 'mismatch', 'does not support']
        }
        return keywords_map.get(error_code, [])

    def _analyze_generic_error(self, error_output: str) -> Optional[ErrorReport]:
        """Анализировать неизвестную ошибку."""
        # Пробуем извлечь текст ошибки
        lines = error_output.split('\n')
        error_line = None

        for line in lines:
            if 'error' in line.lower() or 'failed' in line.lower():
                error_line = line
                break

        if error_line:
            return ErrorReport(
                error_code='UNKNOWN',
                message='Неизвестная ошибка',
                severity=ErrorSeverity.ERROR,
                likely_causes=['Неизвестная причина'],
                suggested_solutions=[
                    'Проверьте логи выше для более подробной информации',
                    'Попробуйте перезагрузить устройство',
                    'Обновите esptool: pip install --upgrade esptool',
                    'Поищите решение в интернете по тексту ошибки'
                ],
                raw_error=error_output
            )

        return None

    def get_friendly_report(self, error_report: ErrorReport) -> str:
        """
        Получить дружественный текстовый отчет об ошибке.

        Args:
            error_report: Отчет об ошибке

        Returns:
            Отформатированный текст
        """
        lines = []

        lines.append(f"\n{'=' * 60}")
        lines.append(f"⚠️  {error_report.severity.value.upper()}: {error_report.message}")
        lines.append(f"{'=' * 60}\n")

        lines.append("Вероятные причины:")
        for i, cause in enumerate(error_report.likely_causes, 1):
            lines.append(f"  {i}. {cause}")

        lines.append("\nПредлагаемые решения:")
        for i, solution in enumerate(error_report.suggested_solutions, 1):
            lines.append(f"  {i}. {solution}")

        lines.append(f"\n{'=' * 60}\n")

        return "\n".join(lines)

    @staticmethod
    def is_error(output: str) -> bool:
        """Проверить содержит ли вывод ошибку."""
        error_indicators = ['error', 'failed', 'fatal', 'exception', 'traceback']
        return any(indicator in output.lower() for indicator in error_indicators)
