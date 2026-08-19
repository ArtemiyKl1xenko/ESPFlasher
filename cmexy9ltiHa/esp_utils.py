"""
ESP chip models and configuration database.
Supports all ESP32 variants and ESP8266.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class ESPChip:
    """ESP chip configuration."""
    name: str
    chip_id: str
    default_flash_mode: str = "dio"
    default_flash_freq: str = "40m"  # 40m, 80m, 120m, 160m depending on chip
    default_flash_size: str = "detect"
    flash_speeds: List[str] = None
    flash_modes: List[str] = None
    description: str = ""

    def __post_init__(self):
        if self.flash_speeds is None:
            self.flash_speeds = ["40m", "80m", "160m"]
        if self.flash_modes is None:
            self.flash_modes = ["dio", "dout", "qio", "qout"]


# Все поддерживаемые чипы ESP
ESP_CHIPS_DATABASE = {
    # ESP32 Standard
    "ESP32": ESPChip(
        name="ESP32",
        chip_id="0x0007",
        default_flash_mode="dio",
        default_flash_freq="80m",
        flash_speeds=["40m", "80m", "160m"],
        description="Original ESP32, dual-core microcontroller"
    ),

    # ESP32-S2
    "ESP32-S2": ESPChip(
        name="ESP32-S2",
        chip_id="0x004d",
        default_flash_mode="dout",
        default_flash_freq="80m",
        flash_speeds=["40m", "80m"],
        description="Single-core ESP32 with USB OTG"
    ),

    # ESP32-S3
    "ESP32-S3": ESPChip(
        name="ESP32-S3",
        chip_id="0x0009",
        default_flash_mode="dio",
        default_flash_freq="80m",
        flash_speeds=["40m", "80m", "120m", "160m"],
        description="Dual-core with AI accelerator"
    ),

    # ESP32-C3
    "ESP32-C3": ESPChip(
        name="ESP32-C3",
        chip_id="0x0005",
        default_flash_mode="dout",
        default_flash_freq="80m",
        flash_speeds=["40m", "80m"],
        description="Single-core RISC-V microcontroller"
    ),

    # ESP32-C6
    "ESP32-C6": ESPChip(
        name="ESP32-C6",
        chip_id="0x0013",
        default_flash_mode="dout",
        default_flash_freq="80m",
        flash_speeds=["40m", "80m"],
        description="RISC-V with 2.4GHz + 5GHz WiFi"
    ),

    # ESP32-H2
    "ESP32-H2": ESPChip(
        name="ESP32-H2",
        chip_id="0x0010",
        default_flash_mode="dout",
        default_flash_freq="80m",
        flash_speeds=["40m", "80m"],
        description="BLE 5.3 only variant"
    ),

    # ESP8266
    "ESP8266": ESPChip(
        name="ESP8266",
        chip_id="0xffff",
        default_flash_mode="dio",
        default_flash_freq="40m",
        flash_speeds=["40m", "80m"],
        flash_modes=["dio", "dout"],
        description="Original WiFi microcontroller"
    ),
}


class ESPChipDetector:
    """Detect and parse ESP chip information from esptool output."""

    @staticmethod
    def parse_chip_id(esptool_output: str) -> Optional[str]:
        """Extract chip ID from esptool output."""
        lines = esptool_output.split('\n')
        for line in lines:
            line_lower = line.lower()

            # Look for chip ID patterns
            if 'chip id' in line_lower:
                # Format: "Chip ID: 0x1234" or "Detected chip type: ESP32"
                if '0x' in line:
                    parts = line.split('0x')
                    if len(parts) > 1:
                        return '0x' + parts[-1].split()[0]

            # Look for chip type
            if 'detected chip type' in line_lower:
                return line.split(':')[-1].strip()

        return None

    @staticmethod
    def detect_chip_model(esptool_output: str) -> Optional[ESPChip]:
        """Detect ESP chip model from esptool output."""
        chip_info = ESPChipDetector.parse_chip_id(esptool_output)
        if not chip_info:
            return None

        # Check by chip name
        for chip_name in ESP_CHIPS_DATABASE:
            if chip_name.lower() in esptool_output.lower():
                return ESP_CHIPS_DATABASE[chip_name]

        # Fallback: return chip info
        chip_lower = chip_info.lower()

        if 'esp32-s3' in chip_lower:
            return ESP_CHIPS_DATABASE['ESP32-S3']
        elif 'esp32-s2' in chip_lower:
            return ESP_CHIPS_DATABASE['ESP32-S2']
        elif 'esp32-c6' in chip_lower:
            return ESP_CHIPS_DATABASE['ESP32-C6']
        elif 'esp32-c3' in chip_lower:
            return ESP_CHIPS_DATABASE['ESP32-C3']
        elif 'esp32-h2' in chip_lower:
            return ESP_CHIPS_DATABASE['ESP32-H2']
        elif 'esp32' in chip_lower:
            return ESP_CHIPS_DATABASE['ESP32']
        elif 'esp8266' in chip_lower:
            return ESP_CHIPS_DATABASE['ESP8266']

        return None

    @staticmethod
    def get_chip_by_name(chip_name: str) -> Optional[ESPChip]:
        """Get chip configuration by name."""
        return ESP_CHIPS_DATABASE.get(chip_name)

    @staticmethod
    def get_all_chip_names() -> List[str]:
        """Get list of all supported chip names."""
        return list(ESP_CHIPS_DATABASE.keys())


def get_flash_params_for_chip(chip: ESPChip) -> Dict[str, str]:
    """Get esptool flash parameters for a chip."""
    return {
        'flash_mode': chip.default_flash_mode,
        'flash_freq': chip.default_flash_freq,
        'flash_size': chip.default_flash_size,
    }
