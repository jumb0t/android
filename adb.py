#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для отключения системных приложений на Android-устройстве через ADB.
Использует объектно-ориентированный подход, логирование, обработку исключений и модульность.
"""

import subprocess
import logging
import sys
from typing import List, Optional


class LoggerSetup:
    """
    Класс для настройки логирования.
    """

    @staticmethod
    def setup_logger(log_file: str = "disable_packages.log") -> logging.Logger:
        """
        Настраивает логгер с указанным файлом и уровнем логирования.

        :param log_file: Путь к файлу логов.
        :return: Настроенный логгер.
        """
        logger = logging.getLogger("DisablePackagesLogger")
        logger.setLevel(logging.DEBUG)

        # Создание обработчика для записи в файл
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.DEBUG)

        # Создание обработчика для вывода в консоль
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(logging.INFO)

        # Форматирование логов
        formatter = logging.Formatter(
            fmt='%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)

        # Добавление обработчиков к логгеру
        logger.addHandler(fh)
        logger.addHandler(ch)

        return logger


class ADBManager:
    """
    Класс для управления взаимодействием с ADB.
    """

    def __init__(self, logger: logging.Logger):
        """
        Инициализирует ADBManager с заданным логгером.

        :param logger: Объект логгера.
        """
        self.logger = logger
        self.device = self.get_connected_device()

    def is_adb_installed(self) -> bool:
        """
        Проверяет, установлен ли ADB и доступен ли в PATH.

        :return: True, если ADB установлен, иначе False.
        """
        try:
            subprocess.run(["adb", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.logger.debug("ADB установлен и доступен.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            self.logger.error("ADB не установлен или недоступен в PATH.")
            return False

    def get_connected_devices(self) -> List[str]:
        """
        Получает список подключённых устройств.

        :return: Список идентификаторов устройств.
        """
        try:
            result = subprocess.run(["adb", "devices"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
            devices = [line.split()[0] for line in lines if line.endswith("device")]
            self.logger.debug(f"Найдено устройств: {devices}")
            return devices
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Ошибка при выполнении команды adb devices: {e.stderr}")
            return []

    def get_connected_device(self) -> Optional[str]:
        """
        Получает идентификатор подключённого устройства, если только одно устройство подключено.

        :return: Идентификатор устройства или None.
        """
        devices = self.get_connected_devices()
        if not devices:
            self.logger.error("Нет подключённых устройств. Пожалуйста, подключите устройство или запустите эмулятор Genymotion.")
            return None
        elif len(devices) > 1:
            self.logger.error("Обнаружено несколько устройств. Пожалуйста, уточните устройство с помощью ADB.")
            self.logger.info("Список подключённых устройств:")
            for device in devices:
                self.logger.info(f" - {device}")
            return None
        else:
            self.logger.info(f"Подключено устройство: {devices[0]}")
            return devices[0]

    def disable_package(self, package_name: str) -> bool:
        """
        Отключает заданный пакет на устройстве.

        :param package_name: Имя пакета для отключения.
        :return: True, если пакет успешно отключён, иначе False.
        """
        if not self.device:
            self.logger.error("Нет подключённого устройства для выполнения команды.")
            return False

        self.logger.info(f"Отключение пакета: {package_name}")
        try:
            # Выполнение команды отключения пакета
            result = subprocess.run(
                ["adb", "-s", self.device, "shell", "pm", "disable-user", "--user", "0", package_name],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            output = result.stdout.lower()
            if "success" in output or "disabled" in output:
                self.logger.info(f"Пакет {package_name} успешно отключён.")
                self.logger.debug(f"Вывод команды: {result.stdout.strip()}")
                return True
            else:
                self.logger.warning(f"Не удалось отключить пакет {package_name}. Вывод команды:")
                self.logger.warning(result.stdout.strip())
                return False
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Ошибка при отключении пакета {package_name}: {e.stderr.strip()}")
            return False

    def check_package_disabled(self, package_name: str) -> bool:
        """
        Проверяет, отключён ли заданный пакет.

        :param package_name: Имя пакета для проверки.
        :return: True, если пакет отключён, иначе False.
        """
        if not self.device:
            self.logger.error("Нет подключённого устройства для выполнения команды.")
            return False

        try:
            result = subprocess.run(
                ["adb", "-s", self.device, "shell", "pm", "list", "packages", "-d"],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            disabled_packages = result.stdout.lower().splitlines()
            package_identifier = f"package:{package_name.lower()}"
            if any(package_identifier in pkg for pkg in disabled_packages):
                self.logger.info(f"Пакет {package_name} успешно отключён.")
                return True
            else:
                self.logger.warning(f"Пакет {package_name} не отключён.")
                return False
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Ошибка при проверке состояния пакета {package_name}: {e.stderr.strip()}")
            return False


class PackageDisabler:
    """
    Класс для управления процессом отключения пакетов.
    """

    def __init__(self, adb_manager: ADBManager, logger: logging.Logger):
        """
        Инициализирует PackageDisabler с заданным ADBManager и логгером.

        :param adb_manager: Объект ADBManager для выполнения ADB-команд.
        :param logger: Объект логгера.
        """
        self.adb_manager = adb_manager
        self.logger = logger
        self.packages = self.load_packages()

    def load_packages(self) -> List[str]:
        """
        Загружает список пакетов для отключения.

        :return: Список уникальных имён пакетов.
        """
        packages = [
            "com.android.camera2",
            "com.android.messaging",
            "com.amaze.filemanager",
            "com.android.printspooler",
            "org.chromium.webview_shell",
            "com.android.quicksearchbox",
            "com.android.gallery3d",
            "com.android.contacts",
            "com.android.phone",
            "com.android.calendar",
            "com.google.android.contacts",
            "com.android.phone"
 #           "com.android.permissioncontroller",
        ]
        unique_packages = list(set(packages))
        self.logger.debug(f"Список пакетов для отключения: {unique_packages}")
        return unique_packages

    def disable_all_packages(self):
        """
        Отключает все пакеты из списка.
        """
        for package in self.packages:
            success = self.adb_manager.disable_package(package)
            if success:
                # Дополнительная проверка, отключён ли пакет
                self.adb_manager.check_package_disabled(package)
            else:
                self.logger.error(f"Пропуск установки пакета {package} из-за ошибки при отключении.")
            self.logger.info("----------------------------------------")

    def verify_all_packages_disabled(self):
        """
        Выполняет дополнительную проверку отключённых пакетов.
        """
        self.logger.info("\nПроверка отключённых пакетов:")
        for package in self.packages:
            is_disabled = self.adb_manager.check_package_disabled(package)
            if is_disabled:
                self.logger.info(f"Пакет {package} успешно отключён.")
            else:
                self.logger.info(f"Пакет {package} не отключён.")


def main():
    """
    Основная функция скрипта.
    """
    # Настройка логирования
    logger = LoggerSetup.setup_logger()

    logger.info("Логирование запущено.")
    logger.info("Логи сохраняются в: ./disable_packages.log")

    # Инициализация ADBManager
    adb_manager = ADBManager(logger)

    # Проверка наличия ADB
    if not adb_manager.is_adb_installed():
        logger.error("ADB не установлен или недоступен. Завершение работы скрипта.")
        sys.exit(1)

    # Проверка подключённых устройств
    if not adb_manager.device:
        sys.exit(1)

    # Инициализация PackageDisabler
    package_disabler = PackageDisabler(adb_manager, logger)

    logger.info("Начало процесса отключения пакетов...")
    package_disabler.disable_all_packages()

    logger.info("Все указанные пакеты были обработаны.")

    # Дополнительная проверка отключённых пакетов
    package_disabler.verify_all_packages_disabled()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logging.getLogger("DisablePackagesLogger").exception(f"Неожиданная ошибка: {e}")
        sys.exit(1)
