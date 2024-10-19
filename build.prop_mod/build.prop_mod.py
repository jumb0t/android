#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
modify_build_prop.py

Автоматическое изменение файлов build.prop на Android устройстве через ADB.

Автор: OpenAI ChatGPT
Дата создания: 2024-10-19

Описание:
Этот скрипт автоматически подключается к Android устройствам через ADB, находит указанные файлы build.prop,
создаёт резервные копии, изменяет их содержимое согласно заданным параметрам и загружает обратно на устройство.
Поддерживает работу с несколькими устройствами ADB, предоставляет продвинутое логгирование с цветовой подсветкой,
а также включает тщательную обработку исключений для обеспечения надёжности.

Требования:
- Python 3.6+
- ADB (Android Debug Bridge) установлен и добавлен в системный PATH.
- Библиотека colorama установлена (pip install colorama)

Использование:
    python3 modify_build_prop.py
"""

import subprocess
import sys
import os
import tempfile
import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional
from colorama import init, Fore, Style

# Инициализация colorama для цветовой подсветки в консоли
init(autoreset=True)


class Logger:
    """
    Класс для настройки и управления логированием.
    Поддерживает вывод в консоль с цветовой подсветкой и в файл.
    """

    def __init__(self, log_file: str, log_format: str):
        """
        Инициализирует логгер.

        :param log_file: Путь к файлу лога.
        :param log_format: Формат строк логов.
        """
        self.logger = logging.getLogger("BuildPropModifier")
        self.logger.setLevel(logging.DEBUG)

        # Форматтер для логов
        formatter = logging.Formatter(log_format)

        # Хэндлер для файла
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)

        # Хэндлер для консоли с цветами
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.ColoredFormatter(log_format))
        self.logger.addHandler(console_handler)

    class ColoredFormatter(logging.Formatter):
        """
        Класс для цветного форматирования вывода в консоль.
        """

        LEVEL_COLORS = {
            logging.DEBUG: Fore.CYAN,
            logging.INFO: Fore.GREEN,
            logging.WARNING: Fore.YELLOW,
            logging.ERROR: Fore.RED,
            logging.CRITICAL: Fore.MAGENTA,
        }

        def __init__(self, fmt: str):
            """
            Инициализирует цветной форматтер.

            :param fmt: Формат строки логов.
            """
            super().__init__(fmt)

        def format(self, record):
            """
            Форматирует запись лога с добавлением цвета в зависимости от уровня.

            :param record: Лог-запись.
            :return: Отформатированная строка.
            """
            color = self.LEVEL_COLORS.get(record.levelno, Fore.WHITE)
            record.msg = color + record.msg + Style.RESET_ALL
            return super().format(record)

    def get_logger(self) -> logging.Logger:
        """
        Возвращает экземпляр логгера.

        :return: logging.Logger
        """
        return self.logger


class ADBHandler:
    """
    Класс для взаимодействия с ADB.
    Поддерживает обнаружение устройств, выполнение команд и обработку ошибок.
    """

    def __init__(self, logger: logging.Logger):
        """
        Инициализирует ADBHandler.

        :param logger: Экземпляр логгера для вывода сообщений.
        """
        self.logger = logger
        self.devices = self.get_connected_devices()

    def get_connected_devices(self) -> List[str]:
        """
        Получает список подключённых устройств через ADB.

        :return: Список идентификаторов устройств.
        """
        try:
            output = subprocess.check_output(["adb", "devices"], stderr=subprocess.STDOUT, text=True)
            lines = output.strip().splitlines()
            devices = [line.split()[0] for line in lines[1:] if 'device' in line and not line.startswith('*')]
            self.logger.debug(f"Обнаруженные устройства: {devices}")
            return devices
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Ошибка при получении списка устройств ADB: {e.output}")
            return []

    def run_command(self, device: str, cmd: List[str]) -> str:
        """
        Выполняет команду ADB на указанном устройстве.

        :param device: Идентификатор устройства.
        :param cmd: Список аргументов команды.
        :return: Вывод команды.
        """
        full_cmd = ["adb", "-s", device] + cmd
        self.logger.debug(f"Выполнение команды: {' '.join(full_cmd)}")
        try:
            output = subprocess.check_output(full_cmd, stderr=subprocess.STDOUT, text=True)
            self.logger.debug(f"Вывод команды: {output.strip()}")
            return output
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Ошибка выполнения команды {' '.join(full_cmd)}: {e.output}")
            raise

    def root_device(self, device: str):
        """
        Перезапускает ADB с правами root на устройстве.

        :param device: Идентификатор устройства.
        """
        try:
            output = self.run_command(device, ["root"])
            self.logger.info(f"ADB root успешно выполнен на устройстве {device}: {output.strip()}")
        except Exception as e:
            self.logger.error(f"Не удалось выполнить ADB root на устройстве {device}: {e}")
            raise

    def remount_device(self, device: str):
        """
        Перемонтирует системные разделы как доступные для записи на устройстве.

        :param device: Идентификатор устройства.
        """
        try:
            output = self.run_command(device, ["remount"])
            self.logger.info(f"Системные разделы успешно перемонтированы на устройстве {device}: {output.strip()}")
        except Exception as e:
            self.logger.error(f"Не удалось перемонтировать системные разделы на устройстве {device}: {e}")
            raise

    def pull_file(self, device: str, remote_path: str, local_path: str):
        """
        Скачивает файл с устройства на локальную машину.

        :param device: Идентификатор устройства.
        :param remote_path: Путь к файлу на устройстве.
        :param local_path: Локальный путь для сохранения файла.
        """
        try:
            self.run_command(device, ["pull", remote_path, local_path])
            self.logger.info(f"Скачивание {remote_path} в {local_path} успешно завершено.")
        except Exception as e:
            self.logger.error(f"Не удалось скачать файл {remote_path} с устройства {device}: {e}")
            raise

    def push_file(self, device: str, local_path: str, remote_path: str):
        """
        Отправляет файл с локальной машины на устройство.

        :param device: Идентификатор устройства.
        :param local_path: Локальный путь к файлу.
        :param remote_path: Путь к файлу на устройстве.
        """
        try:
            self.run_command(device, ["push", local_path, remote_path])
            self.logger.info(f"Отправка {local_path} в {remote_path} на устройстве {device} успешно завершена.")
        except Exception as e:
            self.logger.error(f"Не удалось отправить файл {local_path} на устройство {device}: {e}")
            raise

    def chmod_file(self, device: str, remote_path: str, permissions: str = "644"):
        """
        Устанавливает права доступа для файла build.prop на устройстве.

        :param device: Идентификатор устройства.
        :param remote_path: Путь к файлу на устройстве.
        :param permissions: Права доступа (по умолчанию "644").
        """
        try:
            self.run_command(device, ["shell", "chmod", permissions, remote_path])
            self.logger.info(f"Права доступа для {remote_path} установлены на {permissions}.")
        except Exception as e:
            self.logger.error(f"Не удалось установить права доступа для {remote_path} на устройстве {device}: {e}")
            raise

    def reboot_device(self, device: str):
        """
        Перезагружает устройство.

        :param device: Идентификатор устройства.
        """
        try:
            self.run_command(device, ["reboot"])
            self.logger.info(f"Устройство {device} перезагружается.")
        except Exception as e:
            self.logger.error(f"Не удалось перезагрузить устройство {device}: {e}")
            raise


class BuildPropModifier:
    """
    Класс для модификации файлов build.prop на Android устройстве.
    """

    def __init__(self, adb_handler: ADBHandler, logger: logging.Logger):
        """
        Инициализирует BuildPropModifier.

        :param adb_handler: Экземпляр ADBHandler для взаимодействия с ADB.
        :param logger: Экземпляр логгера для вывода сообщений.
        """
        self.adb = adb_handler
        self.logger = logger
        self.build_prop_paths = [
            "/system/vendor/vendor_dlkm/etc/build.prop",
            "/system/vendor/build.prop",
            "/system/vendor/odm/etc/build.prop",
            "/system/vendor/odm_dlkm/etc/build.prop",
            "/system/system_ext/etc/build.prop",
            "/system/system_dlkm/etc/build.prop",
            "/system/product/etc/build.prop",
        ]
        self.per_file_properties = {
            "/system/vendor/vendor_dlkm/etc/build.prop": {
                "ro.product.vendor_dlkm.brand": "samsung",
                "ro.product.vendor_dlkm.device": "beyond1",
                "ro.product.vendor_dlkm.manufacturer": "samsung",
                "ro.product.vendor_dlkm.model": "SM-G973F",
                "ro.product.vendor_dlkm.name": "beyond1",
                "ro.vendor_dlkm.build.fingerprint": "samsung/beyond1lteeea/beyond1:12/SP1A.210812.016/G973FXXSGHWA3:user/release-keys",
                "ro.vendor_dlkm.build.id": "SP1A.210812.016.G973FXXSGHWA3",
                "ro.vendor_dlkm.build.type": "user",
                "ro.vendor_dlkm.build.tags": "release-keys",
            },
            "/system/vendor/build.prop": {
                "ro.product.vendor.brand": "samsung",
                "ro.product.vendor.device": "beyond1",
                "ro.product.vendor.manufacturer": "samsung",
                "ro.product.vendor.model": "SM-G973F",
                "ro.product.vendor.name": "beyond1lteeea",
                "ro.vendor.build.fingerprint": "samsung/beyond1lteeea/beyond1:12/SP1A.210812.016/G973FXXSGHWA3:user/release-keys",
                "ro.vendor.build.id": "SP1A.210812.016.G973FXXSGHWA3",
                "ro.vendor.build.type": "user",
                "ro.vendor.build.tags": "release-keys",
            },
            "/system/vendor/odm/etc/build.prop": {
                "ro.product.odm.brand": "samsung",
                "ro.product.odm.device": "beyond1",
                "ro.product.odm.manufacturer": "samsung",
                "ro.product.odm.model": "SM-G973F",
                "ro.product.odm.name": "beyond1",
                "ro.odm.build.fingerprint": "samsung/beyond1lteeea/beyond1:12/SP1A.210812.016/G973FXXSGHWA3:user/release-keys",
                "ro.odm.build.id": "SP1A.210812.016.G973FXXSGHWA3",
                "ro.odm.build.type": "user",
                "ro.odm.build.tags": "release-keys",
            },
            "/system/vendor/odm_dlkm/etc/build.prop": {
                "ro.product.odm_dlkm.brand": "samsung",
                "ro.product.odm_dlkm.device": "beyond1",
                "ro.product.odm_dlkm.manufacturer": "samsung",
                "ro.product.odm_dlkm.model": "SM-G973F",
                "ro.product.odm_dlkm.name": "beyond1",
                "ro.odm_dlkm.build.fingerprint": "samsung/beyond1lteeea/beyond1:12/SP1A.210812.016/G973FXXSGHWA3:user/release-keys",
                "ro.odm_dlkm.build.id": "SP1A.210812.016.G973FXXSGHWA3",
                "ro.odm_dlkm.build.type": "user",
                "ro.odm_dlkm.build.tags": "release-keys",
            },
            "/system/system_ext/etc/build.prop": {
                "ro.product.system_ext.brand": "samsung",
                "ro.product.system_ext.device": "beyond1",
                "ro.product.system_ext.manufacturer": "samsung",
                "ro.product.system_ext.model": "SM-G973F",
                "ro.product.system_ext.name": "beyond1lteeea",
                "ro.system_ext.build.fingerprint": "samsung/beyond1lteeea/beyond1:12/SP1A.210812.016/G973FXXSGHWA3:user/release-keys",
                "ro.system_ext.build.id": "SP1A.210812.016.G973FXXSGHWA3",
                "ro.system_ext.build.type": "user",
                "ro.system_ext.build.tags": "release-keys",
            },
            "/system/system_dlkm/etc/build.prop": {
                "ro.product.system_dlkm.brand": "samsung",
                "ro.product.system_dlkm.device": "beyond1",
                "ro.product.system_dlkm.manufacturer": "samsung",
                "ro.product.system_dlkm.model": "SM-G973F",
                "ro.product.system_dlkm.name": "beyond1",
                "ro.system_dlkm.build.fingerprint": "samsung/beyond1lteeea/beyond1:12/SP1A.210812.016/G973FXXSGHWA3:user/release-keys",
                "ro.system_dlkm.build.id": "SP1A.210812.016.G973FXXSGHWA3",
                "ro.system_dlkm.build.type": "user",
                "ro.system_dlkm.build.tags": "release-keys",
            },
            "/system/product/etc/build.prop": {
                "ro.product.product.brand": "samsung",
                "ro.product.product.device": "beyond1",
                "ro.product.product.manufacturer": "samsung",
                "ro.product.product.model": "SM-G973F",
                "ro.product.product.name": "beyond1lteeea",
                "ro.product.build.fingerprint": "samsung/beyond1lteeea/beyond1:12/SP1A.210812.016/G973FXXSGHWA3:user/release-keys",
                "ro.product.build.id": "SP1A.210812.016.G973FXXSGHWA3",
                "ro.product.build.type": "user",
                "ro.product.build.tags": "release-keys",
            },
        }
        self.common_properties = {
            "ro.serialno": "UTI3UWRMIDIAKTWY",
            "ro.build.type": "user",
            "ro.build.id": "SP1A.210812.016.G973FXXSGHWA3",
            "ro.build.tags": "release-keys",
            "ro.build.fingerprint": "samsung/beyond1lteeea/beyond1:12/SP1A.210812.016/G973FXXSGHWA3:user/release-keys",
            "ro.build.type.geny-def": "user",
            "ro.system.build.type.geny-def": "user",
            "ro.build.display.id.geny-def": "beyond0ltexx-user 9 SP1A.210812.016 G973FXXSGHWA3 release-keys",
            "ro.build.display.id": "beyond0ltexx-user 9 SP1A.210812.016 G973FXXSGHWA3 release-keys",
            "ro.build.description.geny-def": "beyond0ltexx-user 9 SP1A.210812.016 G973FXXSGHWA3 release-keys",
            "ro.build.description": "beyond0ltexx-user 9 SP1A.210812.016 G973FXXSGHWA3 release-keys",
            "ro.build.tags.geny-def": "release-keys",
            "ro.build.flavor": "beyond1lteeea-user",
            "ro.build.user": "dpi",
            "ro.build.host": "SWDH4616",
            "ro.build.product": "beyond1lte",
            "ro.product.board": "universal9820",
            "ro.board.platform": "exynos5",
            "ro.build.PDA": "G973FXXSGHWA3",
            "ro.build.official.release": "true",
            "ro.boot.hardware": "exynos9820",
            "ro.hardware": "exynos9820",
            "ro.hardware.chipname": "exynos9820",
            "ro.product.system.name.geny-def": "beyond1lteeea",
            "ro.product.system.device.geny-def": "beyond1",
            "persist.gsm.sim.operator_name": "O2",
            "persist.gsm.sim.phone": "+4207224488990",
            "ro.build.characteristics": "phone",
            "ro.kernel.qemu": "1",
            "ro.product.bootimage.device": "beyond1",
            "ro.product.bootimage.manufacturer": "samsung",
            "ro.product.bootimage.model": "SM-G973F",
            "ro.product.bootimage.name": "beyond1lteeea",
        }

    def backup_file(self, device: str, remote_path: str, backup_dir: Path):
        """
        Создаёт резервную копию файла build.prop на локальной машине.

        :param device: Идентификатор устройства.
        :param remote_path: Путь к файлу на устройстве.
        :param backup_dir: Путь к директории резервных копий.
        """
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            sanitized_path = remote_path.strip("/").replace("/", "_")
            backup_filename = f"{sanitized_path}_backup_{timestamp}.bak"
            local_backup_path = backup_dir / backup_filename

            self.adb.pull_file(device, remote_path, str(local_backup_path))
            self.logger.info(f"Создана резервная копия {remote_path} на {local_backup_path}")
        except Exception as e:
            self.logger.error(f"Не удалось создать резервную копию {remote_path}: {e}")
            raise

    def modify_file(self, local_path: str, properties: Dict[str, str]):
        """
        Модифицирует локальный файл build.prop, обновляя или добавляя заданные свойства.

        :param local_path: Локальный путь к файлу build.prop.
        :param properties: Словарь свойств для обновления.
        """
        try:
            self.logger.debug(f"Чтение файла {local_path} для модификации...")
            with open(local_path, "r", encoding="utf-8") as f:
                lines = f.readlines()

            prop_dict = {}
            for line in lines:
                if line.strip() and not line.startswith("#") and "=" in line:
                    key, value = line.strip().split("=", 1)
                    prop_dict[key] = value

            # Обновление свойств
            prop_dict.update(properties)

            self.logger.debug(f"Запись обновленных свойств в файл {local_path}...")
            with open(local_path, "w", encoding="utf-8") as f:
                f.write("# Измененный build.prop с помощью скрипта\n")
                for key, value in prop_dict.items():
                    f.write(f"{key}={value}\n")

            self.logger.info(f"Файл {local_path} успешно модифицирован.")
        except Exception as e:
            self.logger.error(f"Ошибка при модификации файла {local_path}: {e}")
            raise

    def push_file_back(self, device: str, local_path: str, remote_path: str):
        """
        Отправляет изменённый файл build.prop обратно на устройство.

        :param device: Идентификатор устройства.
        :param local_path: Локальный путь к изменённому файлу.
        :param remote_path: Путь к файлу на устройстве.
        """
        try:
            self.adb.push_file(device, local_path, remote_path)
            self.logger.info(f"Файл {local_path} успешно отправлен обратно на устройство {device} в {remote_path}")
        except Exception as e:
            self.logger.error(f"Не удалось отправить файл {local_path} на устройство {device}: {e}")
            raise

    def set_permissions(self, device: str, remote_path: str):
        """
        Устанавливает права доступа для файла build.prop на устройстве.

        :param device: Идентификатор устройства.
        :param remote_path: Путь к файлу на устройстве.
        """
        try:
            self.adb.chmod_file(device, remote_path, "644")
        except Exception as e:
            self.logger.error(f"Не удалось установить права доступа для {remote_path} на устройстве {device}: {e}")
            raise

    def process_device(self, device: str, backup_dir: Path):
        """
        Обрабатывает все файлы build.prop на указанном устройстве.

        :param device: Идентификатор устройства.
        :param backup_dir: Путь к директории резервных копий.
        """
        try:
            self.logger.info(f"Начало обработки устройства {device}...")
            self.adb.root_device(device)
            self.adb.remount_device(device)

            with tempfile.TemporaryDirectory() as tmpdir:
                for remote_path in self.build_prop_paths:
                    self.backup_file(device, remote_path, backup_dir)

                    local_build_prop = Path(tmpdir) / Path(remote_path).name
                    self.adb.pull_file(device, remote_path, str(local_build_prop))

                    specific_props = self.per_file_properties.get(remote_path, {})
                    self.modify_file(str(local_build_prop), specific_props)
                    self.modify_file(str(local_build_prop), self.common_properties)

                    self.push_file_back(device, str(local_build_prop), remote_path)
                    self.set_permissions(device, remote_path)

            self.logger.info(f"Обработка устройства {device} завершена успешно.")
        except Exception as e:
            self.logger.error(f"Ошибка при обработке устройства {device}: {e}")
            raise


def select_device(devices: List[str], logger: logging.Logger) -> Optional[str]:
    """
    Позволяет пользователю выбрать устройство из списка подключённых устройств.

    :param devices: Список идентификаторов устройств.
    :param logger: Экземпляр логгера для вывода сообщений.
    :return: Выбранный идентификатор устройства или None.
    """
    if not devices:
        logger.error("Нет подключённых устройств ADB.")
        return None
    elif len(devices) == 1:
        logger.info(f"Обнаружено одно устройство: {devices[0]}")
        return devices[0]
    else:
        logger.info("Обнаружено несколько устройств ADB:")
        for idx, device in enumerate(devices, start=1):
            logger.info(f"{idx}. {device}")
        while True:
            try:
                choice = int(input("Выберите устройство по номеру (или 0 для выхода): "))
                if choice == 0:
                    return None
                elif 1 <= choice <= len(devices):
                    return devices[choice - 1]
                else:
                    logger.warning("Некорректный выбор. Пожалуйста, попробуйте снова.")
            except ValueError:
                logger.warning("Пожалуйста, введите числовое значение.")


def setup_logging() -> Logger:
    """
    Настраивает систему логирования.

    :return: Экземпляр класса Logger.
    """
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_dir = Path.cwd() / "build_prop_logs" / timestamp
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "modify_build_prop.log"

    # Определение формата логов
    log_format = "%(asctime)s %(levelname)-6s - %(funcName)-10s - %(filename)-15s:%(lineno)-4d - %(message)s"

    logger_instance = Logger(str(log_file), log_format)
    return logger_instance


def main():
    """
    Основная функция скрипта.
    Настраивает логгирование, обнаруживает устройства, выполняет резервное копирование, модификацию и загрузку файлов build.prop.
    """
    # Настройка логгирования
    logger_instance = setup_logging()
    logger = logger_instance.get_logger()
    logger.info("Запуск скрипта Modify Build Prop")

    try:
        # Инициализация ADBHandler
        adb_handler = ADBHandler(logger)
        if not adb_handler.devices:
            logger.error("Нет подключённых устройств ADB. Завершение скрипта.")
            sys.exit(1)

        # Выбор устройства
        selected_device = select_device(adb_handler.devices, logger)
        if not selected_device:
            logger.info("Нет выбранных устройств. Завершение скрипта.")
            sys.exit(0)

        # Инициализация BuildPropModifier
        modifier = BuildPropModifier(adb_handler, logger)

        # Создание директории для резервных копий
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = Path.cwd() / "build_prop_logs" / timestamp / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)

        # Обработка выбранного устройства
        modifier.process_device(selected_device, backup_dir)

        # Удаление автоматической перезагрузки
        logger.info("Все изменения внесены успешно. Пожалуйста, вручную перезагрузите устройство, если это необходимо.")

        logger.info("Скрипт завершил работу успешно.")

    except Exception as e:
        logger.critical(f"Скрипт завершился с критической ошибкой: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
