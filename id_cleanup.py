#!/usr/bin/env python3
"""
© 2024 Your Name

This script replicates the functionality of the provided Bash script by executing a series of ADB (Android Debug Bridge) commands.
It deletes specific secure settings, removes certain system files, and clears data for various Android packages.

Source: https://gist.github.com/Filiprogrammer/10c255460e7ca4a4ebc913ea567b9425

Requirements:
- Python 3.6+
- ADB installed and added to the system PATH
- Device(s) connected with USB debugging enabled

Usage:
    python3 adb_cleanup.py
"""

import subprocess
import logging
import sys
import time
from typing import List

# Конфигурация логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] [Device: %(device)s] %(message)s',
    handlers=[
        logging.FileHandler("adb_cleanup.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Создание адаптера логгера для добавления информации об устройстве
class DeviceLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        return msg, {'extra': {'device': self.extra.get('device', 'N/A')}}

def run_adb_command(command: List[str], device_id: str, logger: logging.LoggerAdapter) -> None:
    """
    Executes an ADB command for a specific device and handles exceptions.

    Args:
        command (List[str]): The ADB command and its arguments as a list.
        device_id (str): The ID of the device to target.
        logger (logging.LoggerAdapter): The logger adapter with device context.

    Raises:
        subprocess.CalledProcessError: If the ADB command fails.
    """
    try:
        # Вставка флага -s <device_id> после 'adb'
        command_with_device = command.copy()
        adb_index = command_with_device.index("adb")
        command_with_device.insert(adb_index + 1, "-s")
        command_with_device.insert(adb_index + 2, device_id)

        logger.debug(f"Executing command: {' '.join(command_with_device)}")
        result = subprocess.run(
            command_with_device,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        logger.debug(f"Command output: {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {' '.join(command_with_device)}")
        logger.error(f"Error message: {e.stderr.strip()}")
        raise

def check_adb_installed(logger: logging.LoggerAdapter) -> bool:
    """
    Checks if ADB is installed and accessible.

    Args:
        logger (logging.LoggerAdapter): The logger adapter.

    Returns:
        bool: True if ADB is installed, False otherwise.
    """
    try:
        adb_path = subprocess.run(
            ["which", "adb"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        ).stdout.strip()
        logger.debug(f"Using ADB at: {adb_path}")
        return True
    except subprocess.CalledProcessError:
        logger.error("ADB is not installed or not found in PATH.")
        return False

def check_connected_devices() -> List[str]:
    """
    Checks for connected ADB devices.

    Returns:
        List[str]: A list of connected device IDs.

    Raises:
        RuntimeError: If ADB command fails.
    """
    try:
        result = subprocess.run(
            ["adb", "devices"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        devices = []
        for line in result.stdout.strip().split('\n')[1:]:
            if line.strip():
                parts = line.split('\t')
                if len(parts) >= 2:
                    device_id, status = parts
                    if status == "device":
                        devices.append(device_id)
        return devices
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Failed to execute 'adb devices': {e.stderr.strip()}") from e

def delete_secure_settings(device_id: str, logger: logging.LoggerAdapter):
    """
    Deletes specific secure settings on the connected Android device.

    Args:
        device_id (str): The ID of the device to target.
        logger (logging.LoggerAdapter): The logger adapter with device context.
    """
    # Список настроек, которые будут удалены из раздела "secure" настроек устройства
    # Эти настройки могут включать уникальные идентификаторы и другие чувствительные данные
    settings_to_delete = [
        "android_id",           # Уникальный идентификатор устройства Android
        "advertising_id",      # Идентификатор для рекламы, используемый для отслеживания
        "bluetooth_address"    # MAC-адрес Bluetooth интерфейса устройства
    ]
    for setting in settings_to_delete:
        command = ["adb", "shell", "settings", "delete", "secure", setting]
        logger.info(f"Deleting secure setting: {setting}")
        run_adb_command(command, device_id, logger)

def remove_system_files(device_id: str, logger: logging.LoggerAdapter):
    """
    Removes specific system files from the connected Android device using superuser permissions.

    Args:
        device_id (str): The ID of the device to target.
        logger (logging.LoggerAdapter): The logger adapter with device context.
    """
    # Список системных файлов, которые будут удалены.
    # Эти файлы могут содержать информацию о пользователях, учетных записях и синхронизации.
    # Удаление этих файлов может привести к сбросу настроек и данных синхронизации.
    files_to_remove = [
        "/data/system/users/0/accounts.db",                    # База данных учетных записей пользователей
        "/data/system/users/0/accounts.db-journal",            # Журнал транзакций базы данных учетных записей
        "/data/system/users/0/photo.png",                      # Фотография пользователя
        "/data/system/users/0/settings_ssaid.xml",             # Настройки SSAID (Android Advertising ID)
        "/data/system/sync/accounts.xml",                       # Учетные записи для синхронизации
        "/data/system/sync/pending.xml",                        # Ожидающие задачи синхронизации
        "/data/system/sync/stats.bin",                          # Статистические данные синхронизации
        "/data/system/sync/status.bin"                          # Статус текущих синхронизаций
    ]
    for file_path in files_to_remove:
        # Корректное экранирование для обработки пробелов или специальных символов
        command = ["adb", "shell", "su", "-c", f"rm '{file_path}'"]
        logger.info(f"Removing system file: {file_path}")
        run_adb_command(command, device_id, logger)

def clear_packages(device_id: str, logger: logging.LoggerAdapter):
    """
    Clears data for specific Android packages on the connected device.

    Args:
        device_id (str): The ID of the device to target.
        logger (logging.LoggerAdapter): The logger adapter with device context.
    """
    # Список пакетов приложений, данные которых будут очищены.
    # Очистка данных приложения удаляет все пользовательские данные и настройки для данного приложения.
    packages_to_clear = [
        "com.google.android.ext.services",                  # Расширенные сервисы Google
        "com.google.android.ext.shared",                    # Общие библиотеки Google
        "com.google.android.gsf.login",                      # Вход в сервисы Google
        "com.google.android.onetimeinitializer",             # Инициализация одноразовых настроек Google
        "com.android.packageinstaller",                      # Установщик пакетов Android
        "com.android.providers.downloads",                   # Провайдер загрузок Android
        "com.android.vending",                               # Google Play Store
        "com.google.android.backuptransport",                # Транспорт для резервного копирования Google
        "com.google.android.gms",                            # Google Play Services
        "com.google.android.gms.setup",                      # Настройка Google Play Services
        "com.google.android.instantapps.supervisor",         # Супервизор мгновенных приложений Google
        "com.google.android.gsf"                             # Google Services Framework
    ]
    for package in packages_to_clear:
        command = ["adb", "shell", "pm", "clear", package]
        logger.info(f"Clearing package data: {package}")
        run_adb_command(command, device_id, logger)

def wait_for_device(logger: logging.LoggerAdapter, retries: int = 5, delay: int = 5) -> List[str]:
    """
    Waits for devices to be connected, retrying a specified number of times.

    Args:
        logger (logging.LoggerAdapter): The logger adapter.
        retries (int): Number of retry attempts.
        delay (int): Delay in seconds between retries.

    Returns:
        List[str]: A list of connected device IDs.

    Raises:
        RuntimeError: If no devices are found after retries.
    """
    for attempt in range(1, retries + 1):
        logger.info(f"Checking for connected devices (Attempt {attempt}/{retries})...")
        devices = check_connected_devices()
        if devices:
            logger.info(f"Connected devices found: {', '.join(devices)}")
            return devices
        else:
            logger.warning("No connected devices found.")
            if attempt < retries:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)
    raise RuntimeError("No connected devices found after multiple attempts. Please connect a device and ensure USB debugging is enabled.")

def main():
    """
    Main function to execute the ADB cleanup operations.
    """
    # Инициализация логгера без привязки к устройству
    logger = DeviceLoggerAdapter(logging.getLogger(__name__), {'device': 'N/A'})
    logger.info("Starting ADB cleanup script.")

    try:
        # Проверка установки ADB
        if not check_adb_installed(logger):
            logger.error("ADB is not installed or not found in PATH. Please install ADB and ensure it's added to your system PATH.")
            sys.exit(1)

        # Ожидание подключения устройств с повторными попытками
        try:
            devices = wait_for_device(logger, retries=5, delay=5)
        except RuntimeError as e:
            logger.error(e)
            logger.info("Please ensure your device is connected via USB, USB debugging is enabled, and try again.")
            sys.exit(1)

        for device_id in devices:
            device_logger = DeviceLoggerAdapter(logging.getLogger(__name__), {'device': device_id})
            device_logger.info("Starting cleanup operations.")
            try:
                delete_secure_settings(device_id, device_logger)
                remove_system_files(device_id, device_logger)
                clear_packages(device_id, device_logger)
                device_logger.info("Cleanup operations completed successfully.")
            except subprocess.CalledProcessError:
                device_logger.error("An error occurred while executing ADB commands. Check the logs for more details.")
            except Exception as e:
                device_logger.exception(f"Unexpected error: {e}")

        logger.info("ADB cleanup completed for all devices.")

    except Exception as e:
        logger.exception(f"ADB cleanup encountered an error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
