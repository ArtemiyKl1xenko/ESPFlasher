"""
Memory Viewer - визуализация распределения памяти ESP32/ESP8266.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional
from enum import Enum


class MemoryType(Enum):
    """Типы памяти."""
    BOOTLOADER = "Bootloader"
    PARTITION_TABLE = "Partition Table"
    NVDATA = "NV Data"
    PHY_DATA = "PHY Data"
    APPLICATION = "Application"
    SPIFFS = "SPIFFS"
    LITTLEFS = "LittleFS"
    FATFS = "FAT FS"
    OTA = "OTA"
    FREE = "Free"


@dataclass
class MemorySegment:
    """Сегмент памяти."""
    name: str
    start_address: int  # В hex
    size: int  # В байтах
    memory_type: MemoryType
    color: str = "#0078d4"  # Цвет для визуализации
    description: str = ""


class MemoryMap:
    """Карта распределения памяти ESP устройства."""

    # Предустановленные карты памяти для популярных конфигураций
    MEMORY_MAPS = {
        'ESP32-4MB-Default': [
            MemorySegment("Bootloader", 0x1000, 0x4000, MemoryType.BOOTLOADER, "#d13438"),
            MemorySegment("Partition Table", 0x8000, 0x1000, MemoryType.PARTITION_TABLE, "#ffb900"),
            MemorySegment("NV Data", 0x9000, 0x6000, MemoryType.NVDATA, "#107c10"),
            MemorySegment("PHY", 0xf000, 0x1000, MemoryType.PHY_DATA, "#107c10"),
            MemorySegment("Application", 0x10000, 0x140000, MemoryType.APPLICATION, "#0078d4"),
            MemorySegment("OTA", 0x150000, 0x140000, MemoryType.OTA, "#0078d4"),
            MemorySegment("SPIFFS", 0x290000, 0x170000, MemoryType.SPIFFS, "#7030a0"),
        ],
        'ESP32-16MB-Default': [
            MemorySegment("Bootloader", 0x1000, 0x4000, MemoryType.BOOTLOADER, "#d13438"),
            MemorySegment("Partition Table", 0x8000, 0x1000, MemoryType.PARTITION_TABLE, "#ffb900"),
            MemorySegment("NV Data", 0x9000, 0x6000, MemoryType.NVDATA, "#107c10"),
            MemorySegment("PHY", 0xf000, 0x1000, MemoryType.PHY_DATA, "#107c10"),
            MemorySegment("Application", 0x10000, 0x400000, MemoryType.APPLICATION, "#0078d4"),
            MemorySegment("OTA", 0x410000, 0x400000, MemoryType.OTA, "#0078d4"),
            MemorySegment("SPIFFS", 0x810000, 0x7F0000, MemoryType.SPIFFS, "#7030a0"),
        ],
        'ESP8266-4MB': [
            MemorySegment("Bootloader", 0x0, 0x1000, MemoryType.BOOTLOADER, "#d13438"),
            MemorySegment("NV Data", 0x1000, 0x3000, MemoryType.NVDATA, "#107c10"),
            MemorySegment("Application", 0x4000, 0x280000, MemoryType.APPLICATION, "#0078d4"),
            MemorySegment("SPIFFS", 0x284000, 0x16C000, MemoryType.SPIFFS, "#7030a0"),
        ]
    }

    def __init__(self, chip_name: str = "ESP32", memory_size_mb: int = 4):
        """
        Инициализация карты памяти.

        Args:
            chip_name: Имя чипа (ESP32, ESP8266 и т.д.)
            memory_size_mb: Размер памяти в МБ
        """
        self.chip_name = chip_name
        self.memory_size_mb = memory_size_mb
        self.segments: List[MemorySegment] = []

        # Загружаем предустановку
        self._load_preset(chip_name, memory_size_mb)

    def _load_preset(self, chip_name: str, memory_size_mb: int):
        """Загрузить предустановленную карту памяти."""
        preset_key = f"{chip_name}-{memory_size_mb}MB-Default"

        if preset_key in self.MEMORY_MAPS:
            self.segments = [seg for seg in self.MEMORY_MAPS[preset_key]]
        else:
            # Fallback - создаем простую карту
            total_size = memory_size_mb * 1024 * 1024
            self.segments = [
                MemorySegment("Bootloader", 0x1000, 0x4000, MemoryType.BOOTLOADER, "#d13438"),
                MemorySegment("Application", 0x10000, total_size - 0x10000, MemoryType.APPLICATION, "#0078d4"),
            ]

    def get_segment_at(self, address: int) -> Optional[MemorySegment]:
        """
        Получить сегмент памяти по адресу.

        Args:
            address: Адрес в памяти

        Returns:
            MemorySegment или None
        """
        for segment in self.segments:
            if segment.start_address <= address < segment.start_address + segment.size:
                return segment
        return None

    def get_segments_by_type(self, memory_type: MemoryType) -> List[MemorySegment]:
        """
        Получить все сегменты определенного типа.

        Args:
            memory_type: Тип памяти

        Returns:
            Список сегментов
        """
        return [seg for seg in self.segments if seg.memory_type == memory_type]

    def get_free_space(self) -> int:
        """
        Получить размер свободного места.

        Returns:
            Размер в байтах
        """
        total = self.memory_size_mb * 1024 * 1024
        used = sum(seg.size for seg in self.segments)
        return total - used

    def get_used_space(self) -> int:
        """Получить размер используемого места."""
        return sum(seg.size for seg in self.segments)

    def get_summary(self) -> Dict[str, Dict]:
        """
        Получить сводку использования памяти.

        Returns:
            Словарь со сводкой по типам памяти
        """
        summary = {}

        for seg_type in MemoryType:
            segments = self.get_segments_by_type(seg_type)
            if segments:
                total_size = sum(seg.size for seg in segments)
                summary[seg_type.value] = {
                    'total_bytes': total_size,
                    'total_kb': total_size / 1024,
                    'total_mb': total_size / 1024 / 1024,
                    'segments_count': len(segments),
                    'color': segments[0].color
                }

        # Добавляем свободное место
        free_space = self.get_free_space()
        summary['Free'] = {
            'total_bytes': free_space,
            'total_kb': free_space / 1024,
            'total_mb': free_space / 1024 / 1024,
            'segments_count': 1,
            'color': '#cccccc'
        }

        return summary

    def verify_firmware_fit(self, firmware_size: int, address: int = 0x10000) -> bool:
        """
        Проверить поместится ли firmware в памяти.

        Args:
            firmware_size: Размер firmware в байтах
            address: Адрес начала прошивки

        Returns:
            True если влезет
        """
        segment = self.get_segment_at(address)
        if not segment:
            return False

        available_size = segment.start_address + segment.size - address
        return firmware_size <= available_size

    def add_custom_segment(self, segment: MemorySegment):
        """
        Добавить пользовательский сегмент памяти.

        Args:
            segment: Сегмент памяти
        """
        self.segments.append(segment)
        self.segments.sort(key=lambda s: s.start_address)


class MemoryViewer:
    """Визуализатор распределения памяти."""

    def __init__(self, memory_map: MemoryMap):
        """
        Инициализация визуализатора.

        Args:
            memory_map: Карта памяти
        """
        self.memory_map = memory_map

    def get_visual_representation(self, width: int = 80) -> str:
        """
        Получить текстовую визуализацию памяти.

        Args:
            width: Ширина в символах

        Returns:
            Строка с визуализацией
        """
        lines = []
        total_bytes = self.memory_map.memory_size_mb * 1024 * 1024

        lines.append(f"╔ Flash Memory Map ({self.memory_map.memory_size_mb}MB) {'═' * (width - 30)}")
        lines.append("")

        for segment in self.memory_map.segments:
            start_addr = segment.start_address
            end_addr = start_addr + segment.size
            size_kb = segment.size / 1024

            # Рассчитываем позицию в bar
            bar_start = int((start_addr / total_bytes) * width)
            bar_width = max(1, int((segment.size / total_bytes) * width))

            bar = "░" * bar_width

            lines.append(f"│ {segment.name:20} 0x{start_addr:06X} - 0x{end_addr:06X} ({size_kb:8.1f} KB)")
            lines.append(f"│ {bar}")
            lines.append("")

        lines.append(f"╚{' Used: ' + str(self.memory_map.get_used_space() / 1024 / 1024):.1f} MB | Free: {self.memory_map.get_free_space() / 1024 / 1024:.1f} MB {'═' * (width - 50)}")

        return "\n".join(lines)

    def get_html_representation(self) -> str:
        """Получить HTML представление памяти (для экспорта)."""
        html_parts = []
        total_bytes = self.memory_map.memory_size_mb * 1024 * 1024

        html_parts.append(f"<h2>Flash Memory Map - {self.memory_map.chip_name} ({self.memory_map.memory_size_mb}MB)</h2>")
        html_parts.append("<table border='1' cellpadding='5'>")
        html_parts.append("<tr><th>Name</th><th>Address</th><th>Size</th><th>Type</th></tr>")

        for segment in self.memory_map.segments:
            start = f"0x{segment.start_address:06X}"
            end = f"0x{segment.start_address + segment.size:06X}"
            size = f"{segment.size / 1024:.1f} KB"

            html_parts.append(f"<tr style='background-color: {segment.color};'>")
            html_parts.append(f"<td>{segment.name}</td>")
            html_parts.append(f"<td>{start} - {end}</td>")
            html_parts.append(f"<td>{size}</td>")
            html_parts.append(f"<td>{segment.memory_type.value}</td>")
            html_parts.append("</tr>")

        html_parts.append("</table>")

        summary = self.memory_map.get_summary()
        html_parts.append("<h3>Summary</h3>")
        html_parts.append("<ul>")
        for key, data in summary.items():
            html_parts.append(f"<li>{key}: {data['total_mb']:.2f} MB</li>")
        html_parts.append("</ul>")

        return "\n".join(html_parts)
