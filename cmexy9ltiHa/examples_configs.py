#!/usr/bin/env python3
"""
Примеры конфигураций для популярных систем
"""

# ============ Arduino IDE для ESP32 ============

ARDUINO_ESP32_CONFIG = {
    'name': 'Arduino IDE - ESP32',
    'description': 'Конфигурация для Arduino IDE на ESP32',
    'platform': 'espressif32',
    'board': 'esp32devkitc',
    'framework': 'arduino',
    'upload_speed': 460800,
    'monitor_speed': 115200,
    'cmake_build_type': 'Release',

    'platformio_ini': """
[env:esp32-arduino]
platform = espressif32
board = esp32devkitc
framework = arduino

; Upload settings
upload_port = COM3
upload_speed = 460800
upload_protocol = esptool

; Monitor settings
monitor_port = COM3
monitor_speed = 115200

; Build flags
build_flags =
    -DBOARD_HAS_PSRAM
    -mfix-esp32-psram-cache-issue
    -fstack-protector-all
""",

    'esptool_commands': [
        'python -m esptool --port COM3 --baud 460800 write_flash -z 0x1000 bootloader.bin 0x8000 partitions.bin 0x10000 firmware.bin'
    ]
}


# ============ МicroPython ============

MICROPYTHON_ESP32_CONFIG = {
    'name': 'MicroPython - ESP32',
    'description': 'МicroPython firmware для полной поддержки Python',
    'platform': 'espressif32',
    'board': 'esp32devkitc',
    'version': '1.20.x',

    'flash_commands': [
        'python -m esptool --port COM3 --chip esp32 --baud 115200 write_flash -z 0x1000 micropython.bin'
    ],

    'first_boot_commands': [
        """
# После первой загрузки, подключитесь через REPL и выполните:
import machine
import time

# Проверить размер памяти
print(f"Free memory: {machine.mem_free()} bytes")

# Основной цикл
while True:
    print("Hello from MicroPython!")
    time.sleep(1)
""",
    ],

    'requirements_micropython': [
        'urequests',  # HTTP requests
        'micropython-aiohttp',  # Async HTTP
    ],

    'github_releases': 'https://github.com/micropython/micropython/releases'
}


# ============ Tasmota ============

TASMOTA_ESP32_CONFIG = {
    'name': 'Tasmota - ESP32',
    'description': 'Tasmota IOT конфигурация (All-in-One firmware)',
    'platform': 'espressif32',
    'board': 'esp32devkitc',
    'version': '13.x Latest',

    'esptool_commands': [
        'python -m esptool --port COM3 --baud 460800 write_flash -z 0x1000 tasmota32.bin'
    ],

    'initial_setup': """
1. После прошивки, откроется WiFi точка доступа "tasmota-xxxx"
2. Подключитесь и откройте http://192.168.4.1
3. Выберите вашу WiFi сеть
4. Введите пароль
5. Устройство присоединится к сети
6. Откройте http://tasmota.local или http://<ip-адрес>
7. Переходите в Settings и настраивайте компоненты
""",

    'common_templates': {
        'Shelly-1': 'шаблон для Shelly 1',
        'Wemos-D1-Mini': 'шаблон для Wemos D1 Mini',
        'NodeMCU': 'шаблон для NodeMCU',
    },

    'mqtt_settings': """
# MQTT конфигурация для интеграции с Home Assistant
Консоль: 
    MqttHost 192.168.1.100
    MqttPort 1883
    MqttUser username
    MqttPassword password
    MqttTopic tasmota/device_name
""",

    'github_releases': 'https://github.com/arendst/Tasmota/releases'
}


# ============ WLED (RGB LED контроллер) ============

WLED_ESP32_CONFIG = {
    'name': 'WLED - ESP32',
    'description': 'WLED для управления LED полосами',
    'platform': 'espressif32',
    'board': 'esp32devkitc',
    'version': '0.14.x',

    'flash_command': 'python -m esptool --port COM3 --baud 460800 write_flash -z 0x0 wled_0.14.0_esp32_4MB.bin',

    'configuration': """
# После первой загрузки:
1. Подключитесь к WiFi сети "WLED-xxxx"
2. Откройте http://192.168.4.1
3. Выберите вашу WiFi сеть
4. Логин по умолчанию: admin / wledadmin
5. LED Settings:
   - Выберите GPIO пин для данных (обычно GPIO3)
   - Выберите тип LED (WS2812b, APA102 и т.д.)
   - Установите количество LED
6. Сохраните и перезагрузитесь
""",

    'api_examples': """
// Включить все LED белым
GET http://192.168.1.xx/api?seg=0&c=ffffff

// Красный цвет на сегменте 0
GET http://192.168.1.xx/api?seg=0&c=ff0000

// Эффект "Rainbow"  
GET http://192.168.1.xx/api?seg=0&fx=8

// Яркость 50%
GET http://192.168.1.xx/api?bri=128

// Включить/выключить
GET http://192.168.1.xx/api?t=1  // включить
GET http://192.168.1.xx/api?t=0  // выключить
""",

    'github_releases': 'https://github.com/Aircoookie/WLED/releases'
}


# ============ ESPHome ============

ESPHOME_CONFIG = {
    'name': 'ESPHome - ESP32',
    'description': 'ESPHome для интеграции с Home Assistant',
    'platform': 'espressif32',
    'framework': 'espidf',
    'version': '2023.x Latest',

    'esphome_yaml_template': """
esphome:
  name: my-esp32
  friendly_name: "My ESP32 Device"

esp32:
  board: esp32devkitc
  framework:
    type: esp-idf

# Enable logging
logger:

# Enable Home Assistant API
api:
  encryption:
    key: "your-encryption-key"

ota:
  password: "your-ota-password"

wifi:
  ssid: !secret wifi_ssid
  password: !secret wifi_password

# Example: Temperature sensor
sensor:
  - platform: dht
    pin: GPIO4
    temperature:
      name: "Temperature"
    humidity:
      name: "Humidity"
    update_interval: 60s

# Example: Binary sensor (button)
binary_sensor:
  - platform: gpio
    pin: GPIO5
    name: "Button"
    on_press:
      - light.toggle: my_light

# Example: Light (LED)
light:
  - platform: gpio
    pin: GPIO16
    name: "LED"
    id: my_light
""",

    'installation': """
1. Установить ESPHome: pip install esphome
2. Создать проект: esphome create my_config
3. Отредактировать YAML файл
4. Прошить: esphome run my_config.yaml
5. Устройство автоматически найдется в Home Assistant!
""",

    'github_releases': 'https://github.com/esphome/esphome/releases'
}


# ============ Bare Metal (Espressif SDK) ============

ESPRESSIF_SDK_CONFIG = {
    'name': 'Espressif ESP-IDF',
    'description': 'Прямая работа с Espressif SDK',
    'platform': 'espressif32',
    'framework': 'esp-idf',
    'version': 'v5.1 Latest',

    'platformio_ini': """
[env:esp-idf]
platform = espressif32
board = esp32devkitc
framework = esp-idf

; Build settings
build_type = release
""",

    'main_c_example': """
#include <stdio.h>
#include "freertos/FreeRTOS.h"
#include "driver/gpio.h"

void app_main(void) {
    // GPIO configuration
    gpio_pad_select_gpio(GPIO_NUM_2);
    gpio_set_direction(GPIO_NUM_2, GPIO_MODE_OUTPUT);

    printf("ESP32 SDK Example!\\n");

    // Blink LED
    while(1) {
        gpio_set_level(GPIO_NUM_2, 1);
        vTaskDelay(500 / portTICK_PERIOD_MS);

        gpio_set_level(GPIO_NUM_2, 0);
        vTaskDelay(500 / portTICK_PERIOD_MS);
    }
}
"""
}


# ============ Быстрый старт ============

QUICK_START_GUIDE = {
    'step_1_setup': {
        'title': 'Подготовка USB кабеля',
        'instructions': [
            'Используйте качественный USB-A к Micro-USB кабель',
            'Убедитесь что кабель поддерживает передачу данных (не только зарядку)',
            'Подключите к ESP32 DevKit порту USB',
            'Убедитесь что на компьютере появился COM порт'
        ]
    },

    'step_2_drivers': {
        'title': 'Установка драйверов',
        'windows': [
            'Скачайте драйвер для CH340G или CP2102 в зависимости от вашей платы',
            'Установите драйвер',
            'Перезагрузитесь',
            'Проверьте Device Manager - должен появиться COM порт'
        ],
        'linux': [
            'Обычно драйверы установлены в системе',
            'Добавьте пользователя в группу dialout: sudo usermod -a -G dialout $USER',
            'Перезагрузитесь'
        ],
        'mac': [
            'Установите CH340 драйвер отсюда: https://github.com/WCHSoftGroup/ch340ser_mac',
            'Перезагрузитесь'
        ]
    },

    'step_3_first_flash': {
        'title': 'Первая прошивка',
        'instructions': [
            '1. Откройте ESP Flasher Pro',
            '2. Flash tab → "🔍 Обнаружить"',
            '3. Выберите встроенный preset (Arduino или MicroPython)',
            '4. Кнопка "⚡ Прошить"',
            '5. Ждите ~ 1 минуту',
            '6. "Success!" - готово!'
        ]
    }
}


# ============ Шпаргалка ============

CHEATSHEET = {
    'essential_commands': {
        'detect_chip': 'esptool.py --port COM3 chip_id',
        'read_flash': 'esptool.py --port COM3 read_flash 0 4194304 backup.bin',
        'erase_flash': 'esptool.py --port COM3 erase_flash',
        'write_firmware': 'esptool.py --port COM3 write_flash 0x1000 firmware.bin',
    },

    'gpio_pins': {
        'esp32': [
            'GPIO0 - BOOT pin (удерживайте для режима загрузки)',
            'GPIO2 - LED on DevKit',
            'GPIO4,5 - UART2',
            'GPIO16,17 - UART2 (alt)',
            'GPIO35-39 - Input only',
        ],
        'esp8266': [
            'GPIO0 - BOOT pin',
            'GPIO2 - LED on DevKit',
            'D0-D8 - Основные GPIO',
        ]
    },

    'memory_addresses': {
        'bootloader': '0x1000',
        'partition_table': '0x8000',
        'app_firmware': '0x10000',
        'nvs': '0x9000',
        'phy_data': '0xf000',
        'spiffs': '0x290000'
    }
}


if __name__ == '__main__':
    print("=" * 60)
    print("ESP Flasher Pro - Configuration Examples")
    print("=" * 60)
    print("\nДоступные конфигурации:")
    print("1. Arduino IDE")
    print("2. MicroPython")
    print("3. Tasmota")
    print("4. WLED")
    print("5. ESPHome")
    print("6. ESP-IDF (Bare Metal)")
    print("\nИспользуйте эти конфигурации как шаблоны для ваших проектов!")
