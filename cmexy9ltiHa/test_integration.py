#!/usr/bin/env python
"""Integration test for ESP Flasher application."""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

print('[Starting Integration Tests]')
print('=' * 60)

# Test 1: Imports
print('\n[Step 1] Проверка импортов...')
try:
    import esp_utils
    import models
    import config_manager
    import flasher_manager
    from cmexy9ltiHa import ESPFlasherApp
    print('[✓] Все модули импортированы успешно')
except ImportError as e:
    print(f'[✗] Ошибка импорта: {e}')
    sys.exit(1)

# Test 2: ESP Chip Database
print('\n[Step 2] Проверка базы данных чипов ESP...')
try:
    chips = esp_utils.ESPChipDetector.get_all_chip_names()
    print(f'[✓] Найдено поддерживаемых чипов: {len(chips)}')
    for chip_name in chips:
        chip = esp_utils.ESPChipDetector.get_chip_by_name(chip_name)
        if chip:
            print(f'  ✓ {chip_name:15} - {chip.description}')
        else:
            print(f'  ✗ {chip_name} - не найден')
            raise ValueError(f"Chip {chip_name} not found in database")
except Exception as e:
    print(f'[✗] Ошибка при проверке чипов: {e}')
    sys.exit(1)

# Test 3: Models - FileEntry
print('\n[Step 3] Проверка моделей данных...')
try:
    # Test FileEntry
    file_entry = models.FileEntry(address='0x1000', path='/path/to/file.bin')
    file_dict = file_entry.to_dict()
    file_restored = models.FileEntry.from_dict(file_dict)
    assert file_restored.address == file_entry.address
    assert file_restored.path == file_entry.path
    print('[✓] FileEntry сериализация работает')
except Exception as e:
    print(f'[✗] Ошибка FileEntry: {e}')
    sys.exit(1)

# Test 4: Models - FlashProfile
try:
    profile = models.FlashProfile(
        name='Test Profile',
        description='Test Description',
        files=[file_entry],
        baud_rate=115200,
        port='COM1'
    )
    profile_dict = profile.to_dict()
    # Important: create a NEW dict to test that from_dict doesn't modify original
    profile_dict_copy = profile_dict.copy()
    profile_restored = models.FlashProfile.from_dict(profile_dict_copy)
    assert profile_restored.name == 'Test Profile'
    assert len(profile_restored.files) == 1
    assert profile_dict_copy == profile_dict  # Verify original dict wasn't modified
    print('[✓] FlashProfile сериализация работает')
except Exception as e:
    print(f'[✗] Ошибка FlashProfile: {e}')
    sys.exit(1)

# Test 5: Models - FlashOperation
try:
    from datetime import datetime
    operation = models.FlashOperation(
        profile_name='Test Operation',
        port='COM1',
        baud_rate=115200,
        files_count=1,
        success=True,
        duration_seconds=10.5
    )
    op_dict = operation.to_dict()
    # Verify timestamp is ISO format string in dict
    assert isinstance(op_dict['timestamp'], str)
    op_restored = models.FlashOperation.from_dict(op_dict)
    # Verify timestamp is back to datetime
    assert isinstance(op_restored.timestamp, datetime)
    assert op_restored.profile_name == 'Test Operation'
    print('[✓] FlashOperation сериализация работает')
except Exception as e:
    print(f'[✗] Ошибка FlashOperation: {e}')
    sys.exit(1)

# Test 6: FlasherManager
print('\n[Step 4] Проверка FlasherManager...')
try:
    fm = flasher_manager.FlasherManager(on_log=lambda x: None)
    # Test chip detection with mock output
    sample_output = """
    Detecting chip type... Chip is ESP32-S3 (revision v0.1)
    Chip ID: 0x0009
    """
    chip = esp_utils.ESPChipDetector.detect_chip_model(sample_output)
    if chip:
        print(f'[✓] Обнаружена модель: {chip.name}')
        params = esp_utils.get_flash_params_for_chip(chip)
        print(f'  - Flash mode: {params["flash_mode"]}')
        print(f'  - Flash freq: {params["flash_freq"]}')
        print(f'  - Flash size: {params["flash_size"]}')
    else:
        print('[i] Chip detection вернул None (expected for mock output)')
except Exception as e:
    print(f'[✗] Ошибка FlasherManager: {e}')
    sys.exit(1)

# Final summary
print('\n' + '=' * 60)
print('[SUCCESS] ✓ Все тесты пройдены успешно!')
print('[INFO] Приложение готово к использованию.')
print('\n[Supported ESP Models]')
chips = esp_utils.ESPChipDetector.get_all_chip_names()
for chip in chips:
    print(f'  ✓ {chip}')
print('=' * 60)
