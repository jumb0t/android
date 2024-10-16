```markdown
# ADB Cleanup Script

![License](https://img.shields.io/github/license/yourusername/adb-cleanup)
![Python Version](https://img.shields.io/badge/python-3.6%2B-blue)
![Status](https://img.shields.io/badge/status-Stable-green)

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Functions](#functions)
  - [check_adb_installed](#check_adb_installed)
  - [check_connected_devices](#check_connected_devices)
  - [wait_for_device](#wait_for_device)
  - [run_adb_command](#run_adb_command)
  - [delete_secure_settings](#delete_secure_settings)
  - [remove_system_files](#remove_system_files)
  - [clear_packages](#clear_packages)
- [Logging](#logging)
- [Error Handling](#error-handling)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

## Overview

The **ADB Cleanup Script** is a Python-based tool designed to automate the cleanup of specific settings, system files, and package data on Android devices using the Android Debug Bridge (ADB). This script is especially useful for developers, testers, and power users who need to reset devices to a clean state for testing or other purposes.

## Features

- **Multi-Device Support**: Detects and handles multiple connected Android devices simultaneously.
- **Comprehensive Cleanup**:
  - Deletes specific secure settings.
  - Removes designated system files.
  - Clears data for various Android packages.
- **Robust Logging**: Logs all actions and errors to both the console and a log file (`adb_cleanup.log`) with detailed information, including device-specific contexts.
- **Enhanced Error Handling**: Implements retries and provides informative error messages to guide users in resolving issues.
- **Configurable**: Easily modify settings, files, and packages to target through the script.

## Requirements

- **Python**: Version 3.6 or higher.
- **ADB (Android Debug Bridge)**: Installed and added to the system's `PATH`.
- **Android Device(s)**: Connected via USB with USB Debugging enabled and, if required, rooted with `su` access.

## Installation

1. **Clone the Repository**:

   ```bash
   git clone https://github.com/yourusername/adb-cleanup.git
   cd adb-cleanup
   ```

2. **Install Python Dependencies**:

   This script relies on Python's standard library, so no additional packages are required. However, it's recommended to use a virtual environment.

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Ensure ADB is Installed**:

   - **Download ADB**: If you haven't installed ADB, download the [Android SDK Platform-Tools](https://developer.android.com/studio/releases/platform-tools).
   - **Add ADB to PATH**:
     - **Linux/macOS**:
       ```bash
       export PATH=$PATH:/path/to/platform-tools
       ```
       Add the above line to your `~/.bashrc` or `~/.zshrc`.
     - **Windows**:
       - Navigate to **System Properties** > **Advanced** > **Environment Variables**.
       - Edit the `Path` variable and add the path to `platform-tools`.

## Configuration

The script is configured with predefined lists of settings, system files, and packages to target. To customize the cleanup process:

1. **Open the Script**:

   ```bash
   nano adb_cleanup.py
   ```

2. **Modify the Lists**:

   - **Secure Settings**:

     ```python
     settings_to_delete = [
         "android_id",
         "advertising_id",
         "bluetooth_address"
     ]
     ```

   - **System Files**:

     ```python
     files_to_remove = [
         "/data/system/users/0/accounts.db",
         "/data/system/users/0/accounts.db-journal",
         "/data/system/users/0/photo.png",
         "/data/system/users/0/settings_ssaid.xml",
         "/data/system/sync/accounts.xml",
         "/data/system/sync/pending.xml",
         "/data/system/sync/stats.bin",
         "/data/system/sync/status.bin"
     ]
     ```

   - **Packages**:

     ```python
     packages_to_clear = [
         "com.google.android.ext.services",
         "com.google.android.ext.shared",
         "com.google.android.gsf.login",
         "com.google.android.onetimeinitializer",
         "com.android.packageinstaller",
         "com.android.providers.downloads",
         "com.android.vending",
         "com.google.android.backuptransport",
         "com.google.android.gms",
         "com.google.android.gms.setup",
         "com.google.android.instantapps.supervisor",
         "com.google.android.gsf"
     ]
     ```

   Adjust these lists according to your specific cleanup needs.

## Usage

1. **Connect Your Android Device(s)**:

   - Use a USB cable that supports data transfer.
   - Ensure USB Debugging is enabled:
     - Go to **Settings** > **About phone**.
     - Tap **Build number** seven times to enable **Developer options**.
     - Navigate to **Settings** > **Developer options**.
     - Enable **USB Debugging**.

2. **Authorize ADB Debugging**:

   - When prompted on your device, authorize the connected computer for USB debugging.

3. **Run the Script**:

   ```bash
   python3 adb_cleanup.py
   ```

4. **Monitor the Output**:

   - The script will log actions to both the console and the `adb_cleanup.log` file located in the script's directory.

## Functions

### `check_adb_installed(logger)`

**Description**: Verifies if ADB is installed and accessible in the system's `PATH`.

**Arguments**:
- `logger` (`logging.LoggerAdapter`): The logger instance for logging messages.

**Returns**:
- `bool`: `True` if ADB is installed, `False` otherwise.

**Raises**:
- Logs an error if ADB is not found.

### `check_connected_devices()`

**Description**: Retrieves a list of connected Android devices recognized by ADB.

**Arguments**: None

**Returns**:
- `List[str]`: A list of device IDs that are currently connected and authorized.

**Raises**:
- `RuntimeError`: If the ADB command fails to execute.

### `wait_for_device(logger, retries=5, delay=5)`

**Description**: Waits for Android devices to be connected, retrying a specified number of times with delays between attempts.

**Arguments**:
- `logger` (`logging.LoggerAdapter`): The logger instance for logging messages.
- `retries` (`int`): Number of retry attempts (default is 5).
- `delay` (`int`): Delay in seconds between retries (default is 5).

**Returns**:
- `List[str]`: A list of connected device IDs.

**Raises**:
- `RuntimeError`: If no devices are found after the specified number of retries.

### `run_adb_command(command, device_id, logger)`

**Description**: Executes an ADB command for a specific device and handles exceptions.

**Arguments**:
- `command` (`List[str]`): The ADB command and its arguments as a list.
- `device_id` (`str`): The ID of the device to target.
- `logger` (`logging.LoggerAdapter`): The logger instance for logging messages.

**Returns**: None

**Raises**:
- `subprocess.CalledProcessError`: If the ADB command fails.

### `delete_secure_settings(device_id, logger)`

**Description**: Deletes specific secure settings on the connected Android device.

**Arguments**:
- `device_id` (`str`): The ID of the device to target.
- `logger` (`logging.LoggerAdapter`): The logger instance with device context.

**Returns**: None

**Raises**:
- Exceptions related to command execution.

**Parameters Explained**:

```python
settings_to_delete = [
    "android_id",           # Уникальный идентификатор устройства Android
    "advertising_id",      # Идентификатор для рекламы, используемый для отслеживания
    "bluetooth_address"    # MAC-адрес Bluetooth интерфейса устройства
]
```

- **android_id**: Уникальный идентификатор устройства Android, который используется различными приложениями для отслеживания устройства.
- **advertising_id**: Идентификатор, предоставляемый Google, используемый для персонализированной рекламы и аналитики.
- **bluetooth_address**: MAC-адрес Bluetooth интерфейса устройства, который может использоваться для идентификации устройства в сетях Bluetooth.

### `remove_system_files(device_id, logger)`

**Description**: Removes specific system files from the connected Android device using superuser permissions.

**Arguments**:
- `device_id` (`str`): The ID of the device to target.
- `logger` (`logging.LoggerAdapter`): The logger instance with device context.

**Returns**: None

**Raises**:
- Exceptions related to command execution.

**Parameters Explained**:

```python
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
```

- **accounts.db**: База данных, содержащая учетные записи пользователей, добавленные на устройство.
- **accounts.db-journal**: Журнал транзакций для базы данных учетных записей, используемый для восстановления после сбоев.
- **photo.png**: Изображение профиля пользователя.
- **settings_ssaid.xml**: Файл настроек, содержащий SSAID (Android Advertising ID), который используется для рекламных целей.
- **accounts.xml**: XML-файл, содержащий информацию об учетных записях для синхронизации.
- **pending.xml**: XML-файл, содержащий ожидающие задачи синхронизации.
- **stats.bin**: Бинарный файл, содержащий статистические данные синхронизации.
- **status.bin**: Бинарный файл, содержащий статус текущих синхронизаций.

### `clear_packages(device_id, logger)`

**Description**: Clears data for specific Android packages on the connected device.

**Arguments**:
- `device_id` (`str`): The ID of the device to target.
- `logger` (`logging.LoggerAdapter`): The logger instance with device context.

**Returns**: None

**Raises**:
- Exceptions related to command execution.

**Parameters Explained**:

```python
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
```

- **com.google.android.ext.services**: Расширенные сервисы Google, предоставляющие дополнительные функции для приложений.
- **com.google.android.ext.shared**: Общие библиотеки Google, используемые несколькими приложениями для обеспечения совместимости и функциональности.
- **com.google.android.gsf.login**: Компонент, отвечающий за аутентификацию и вход в сервисы Google.
- **com.google.android.onetimeinitializer**: Компонент, выполняющий одноразовую инициализацию сервисов Google при первом запуске.
- **com.android.packageinstaller**: Приложение, отвечающее за установку и управление пакетами приложений на устройстве.
- **com.android.providers.downloads**: Провайдер загрузок Android, отвечающий за управление загрузками файлов.
- **com.android.vending**: Приложение Google Play Store, используемое для установки и обновления приложений.
- **com.google.android.backuptransport**: Компонент, отвечающий за транспорт данных резервного копирования в сервисах Google.
- **com.google.android.gms**: Google Play Services, предоставляющие базовые функции и API для приложений Google и сторонних разработчиков.
- **com.google.android.gms.setup**: Компонент, отвечающий за настройку и конфигурацию Google Play Services.
- **com.google.android.instantapps.supervisor**: Супервизор мгновенных приложений Google, управляющий запуском и обновлением мгновенных приложений.
- **com.google.android.gsf**: Google Services Framework, основополагающий компонент, необходимый для работы сервисов Google.

## Logging

The script utilizes Python's `logging` module to provide detailed logs of its operations. Logs are output to both the console and a log file named `adb_cleanup.log` located in the script's directory.

**Log Levels**:

- `INFO`: General information about the script's progress.
- `DEBUG`: Detailed debugging information (can be enabled by setting the logging level to `DEBUG`).
- `WARNING`: Warnings about potential issues.
- `ERROR`: Errors encountered during execution.
- `CRITICAL`: Critical issues that may cause the script to terminate.

**Custom Logger Adapter**:

A `DeviceLoggerAdapter` is used to prepend device-specific information to each log message, enhancing traceability when handling multiple devices.

## Error Handling

The script is designed to handle errors gracefully and provide informative messages to the user. Key aspects include:

- **ADB Installation Check**: Verifies if ADB is installed before proceeding. If not found, logs an error and exits.
- **Device Detection with Retries**: Attempts to detect connected devices multiple times with delays, logging each attempt. If no devices are found after all retries, logs an error and exits.
- **Command Execution Errors**: Captures and logs errors from failed ADB commands without terminating the entire script. Continues processing other devices if available.
- **Unexpected Exceptions**: Catches and logs any unforeseen exceptions, providing stack traces for debugging.

## Contributing

Contributions are welcome! If you find a bug or have a feature request, please open an issue or submit a pull request.

### Steps to Contribute

1. **Fork the Repository**:

   Click the "Fork" button at the top-right corner of the repository page.

2. **Clone Your Fork**:

   ```bash
   git clone https://github.com/yourusername/adb-cleanup.git
   cd adb-cleanup
   ```

3. **Create a New Branch**:

   ```bash
   git checkout -b feature/YourFeatureName
   ```

4. **Make Your Changes**:

   Implement your feature or bug fix.

5. **Commit Your Changes**:

   ```bash
   git commit -m "Add feature: YourFeatureName"
   ```

6. **Push to Your Fork**:

   ```bash
   git push origin feature/YourFeatureName
   ```

7. **Open a Pull Request**:

   Navigate to your fork on GitHub and click "Compare & pull request".

## License

This project is licensed under the [MIT License](LICENSE).

## Contact

For any questions or support, please open an issue on the [GitHub repository](https://github.com/yourusername/adb-cleanup/issues) or contact [your.email@example.com](mailto:your.email@example.com).

---

© 2024 Your Name. All rights reserved.
```