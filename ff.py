#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Скрипт для изменения системных свойств Android-устройства через ADB с целью эмуляции Samsung Galaxy S10.
Использует объектно-ориентированный подход, логирование, обработку исключений и модульность.

ВНИМАНИЕ: Изменение системных файлов может привести к нестабильной работе устройства или его неработоспособности.
Убедитесь, что понимаете риски и имеете резервные копии важных данных перед выполнением этого скрипта.
"""

import subprocess
import logging
import sys
import os
import time
from typing import List, Optional

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("android_build_prop_modifier.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class ADBManager:
    """
    Класс для управления взаимодействием с ADB.
    """

    def __init__(self):
        self.device = self.get_connected_device()

    def is_adb_installed(self) -> bool:
        """
        Проверяет, установлен ли ADB и доступен ли в PATH.
        """
        try:
            subprocess.run(["adb", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            logger.debug("ADB установлен и доступен.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("ADB не установлен или недоступен в PATH.")
            return False

    def get_connected_devices(self) -> List[str]:
        """
        Получает список подключённых устройств.
        """
        try:
            result = subprocess.run(["adb", "devices"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            lines = result.stdout.strip().split('\n')[1:]  # Пропускаем заголовок
            devices = [line.split()[0] for line in lines if line.endswith("device")]
            logger.debug(f"Найдено устройств: {devices}")
            return devices
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при выполнении команды adb devices: {e.stderr}")
            return []

    def get_connected_device(self) -> Optional[str]:
        """
        Получает идентификатор подключённого устройства, если только одно устройство подключено.
        """
        devices = self.get_connected_devices()
        if not devices:
            logger.error("Нет подключённых устройств. Пожалуйста, подключите устройство или запустите эмулятор Genymotion.")
            return None
        elif len(devices) > 1:
            logger.error("Обнаружено несколько устройств. Пожалуйста, уточните устройство с помощью ADB.")
            subprocess.run(["adb", "devices"])
            return None
        else:
            logger.info(f"Подключено устройство: {devices[0]}")
            return devices[0]

    def remount_system_rw(self) -> bool:
        """
        Перемонтирует системный раздел в режим чтения-записи.
        """
        try:
            subprocess.run(["adb", "root"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            subprocess.run(["adb", "remount"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info("Системный раздел успешно перемонтирован в режим чтения-записи.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Не удалось перемонтировать системный раздел: {e.stderr}")
            return False

    def pull_file(self, remote_path: str, local_path: str) -> bool:
        """
        Скачивает файл с устройства на локальную машину.
        """
        try:
            subprocess.run(["adb", "pull", remote_path, local_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info(f"Файл {remote_path} успешно скачан на {local_path}.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при скачивании файла {remote_path}: {e.stderr}")
            return False

    def push_file(self, local_path: str, remote_path: str) -> bool:
        """
        Загружает файл с локальной машины на устройство.
        """
        try:
            subprocess.run(["adb", "push", local_path, remote_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info(f"Файл {local_path} успешно загружен на {remote_path}.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при загрузке файла {local_path}: {e.stderr}")
            return False

    def set_permissions(self, remote_path: str, permissions: str = "644") -> bool:
        """
        Устанавливает разрешения на файл на устройстве.
        """
        try:
            subprocess.run(["adb", "shell", "chmod", permissions, remote_path], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info(f"Разрешения для {remote_path} установлены на {permissions}.")
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при установке разрешений для {remote_path}: {e.stderr}")
            return False

    def reboot_device(self):
        """
        Перезагружает устройство.
        """
        try:
            subprocess.run(["adb", "reboot"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            logger.info("Устройство перезагружается...")
            # Подождать, пока устройство перезагрузится
            time.sleep(60)  # Увеличено время ожидания для надежности
        except subprocess.CalledProcessError as e:
            logger.error(f"Ошибка при перезагрузке устройства: {e.stderr}")


class BuildPropManager:
    """
    Класс для управления файлом build.prop.
    """

    def __init__(self, local_path: str):
        """
        Инициализирует BuildPropManager с указанным локальным путём к build.prop.
        """
        self.local_path = local_path

    def backup_build_prop(self, backup_path: str) -> bool:
        """
        Создаёт резервную копию build.prop.
        """
        try:
            with open(self.local_path, 'r', encoding='utf-8') as original, open(backup_path, 'w', encoding='utf-8') as backup:
                backup.write(original.read())
            logger.info(f"Резервная копия создана: {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Не удалось создать резервную копию build.prop: {e}")
            return False

    def parse_build_prop(self) -> dict:
        """
        Парсит build.prop и возвращает словарь свойств.
        """
        props = {}
        try:
            with open(self.local_path, 'r', encoding='utf-8') as file:
                for line in file:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        props[key.strip()] = value.strip()
            logger.debug("build.prop успешно распарсен.")
        except Exception as e:
            logger.error(f"Ошибка при парсинге build.prop: {e}")
        return props

    def modify_build_prop(self, modifications: dict) -> bool:
        """
        Вносит изменения в build.prop согласно переданным модификациям.
        Изменяет существующие свойства или добавляет новые, если их нет.
        """
        try:
            props = self.parse_build_prop()

            # Вносим изменения
            for key, value in modifications.items():
                if key in props:
                    logger.debug(f"Изменение свойства: {key}={props[key]} -> {key}={value}")
                else:
                    logger.debug(f"Добавление нового свойства: {key}={value}")
                props[key] = value

            # Записываем обратно
            with open(self.local_path, 'w', encoding='utf-8') as file:
                for key, value in props.items():
                    file.write(f"{key}={value}\n")

            logger.info("Файл build.prop успешно модифицирован.")
            return True
        except Exception as e:
            logger.error(f"Ошибка при модификации build.prop: {e}")
            return False


class SamsungS10Emulator:
    """
    Класс для эмуляции Samsung Galaxy S10 путём изменения build.prop.
    """

    def __init__(self, adb_manager: ADBManager, build_prop_manager: BuildPropManager):
        self.adb_manager = adb_manager
        self.build_prop_manager = build_prop_manager
        self.modifications = self.get_s10_modifications()

    def get_s10_modifications(self) -> dict:
        """
        Возвращает словарь модификаций для build.prop, эмулирующих Samsung Galaxy S10.
        """
        modifications = {
            # Основные свойства устройства
            "ro.product.model": "SM-G973F",
            "ro.product.name": "dreamlte",
            "ro.product.device": "dreamlte",
            "ro.product.brand": "samsung",
            "ro.product.manufacturer": "samsung",
            "ro.product.cpu.abi": "arm64-v8a",
            "ro.product.cpu.abilist": "arm64-v8a,armeabi-v7a,armeabi",
            "ro.build.fingerprint": "samsung/dreamlte/dreamlte:10/QP1A.190711.020/G973FXXU3CRH1:user/release-keys",
            "ro.build.version.release": "10",
            "ro.build.version.sdk": "29",
            "ro.build.version.incremental": "G973FXXU3CRH1",
            "ro.build.type": "user",
            "ro.build.tags": "release-keys",
            "ro.build.display.id": "QP1A.190711.020.G973FXXU3CRH1",
            "ro.build.description": "dreamlte-user 10 QP1A.190711.020 G973FXXU3CRH1 release-keys",
            "ro.build.product": "dreamlte",
            "ro.build.user": "builder",
            "ro.build.host": "builder-server",
            "ro.build.date": "Mon Nov 20 11:56:52 UTC 2023",
            "ro.build.date.utc": "1700481412",
            # Дополнительные свойства для Samsung S10
            "ro.build.version.release_or_codename": "10",
            "ro.build.version.security_patch": "2023-05-05",
            "ro.build.flavor": "dreamlte-user",
            "ro.hardware": "samsung",
            "ro.opengles.version": "196610",
            "ro.genymotion.device.version": "1",
            "ro.genymotion.version": "3.1.0",
            "ro.product.first_api_level": "16",
            "ro.ril.hsxpa": "1",
            "ro.ril.gprsclass": "10",
            # Настройки безопасности и отладки
            "persist.sys.root_access": "3",
            "service.adb.root": "1",
            "ro.debuggable": "1",
            "dalvik.vm.heapsize": "256m",
            "dalvik.vm.dex2oat-Xms": "64m",
            "dalvik.vm.dex2oat-Xmx": "512m",
            "dalvik.vm.usejit": "true",
            "dalvik.vm.usejitprofiles": "true",
            # Дополнительные настройки
            "net.bt.name": "Android",
            "ro.allow.mock.location": "0",
            "ro.secure": "1",
            "security.perf_harden": "1",
            "dalvik.vm.lockprof.threshold": "500",
            "dalvik.vm.madvise.vdexfile.size": "104857600",
            "dalvik.vm.madvise.odexfile.size": "104857600",
            "dalvik.vm.madvise.artfile.size": "4294967295",
            # Добавленный параметр
            "ro.product.system.manufacturer.geny-def": "samsung",
            # Добавьте другие свойства по необходимости
        }
        return modifications

    def emulate_samsung_s10(self) -> bool:
        """
        Выполняет процесс эмуляции Samsung Galaxy S10.
        """
        logger.info("Начало процесса эмуляции Samsung Galaxy S10.")

        # Перемонтирование системного раздела в режим чтения-записи
        if not self.adb_manager.remount_system_rw():
            logger.error("Не удалось перемонтировать системный раздел. Завершение работы.")
            return False

        # Скачивание текущего build.prop
        remote_build_prop = "/system/build.prop"
        local_build_prop = "build.prop"
        backup_build_prop = "build.prop.bak"

        if not self.adb_manager.pull_file(remote_build_prop, local_build_prop):
            logger.error("Не удалось скачать build.prop. Завершение работы.")
            return False

        # Создание резервной копии
        build_prop_manager = BuildPropManager(local_path=local_build_prop)
        if not build_prop_manager.backup_build_prop(backup_build_prop):
            logger.error("Не удалось создать резервную копию build.prop. Завершение работы.")
            return False

        # Модификация build.prop
        if not build_prop_manager.modify_build_prop(self.modifications):
            logger.error("Не удалось модифицировать build.prop. Завершение работы.")
            return False

        # Загрузка изменённого build.prop обратно на устройство
        if not self.adb_manager.push_file(local_build_prop, remote_build_prop):
            logger.error("Не удалось загрузить изменённый build.prop на устройство. Завершение работы.")
            return False

        # Установка разрешений на build.prop
        if not self.adb_manager.set_permissions(remote_build_prop, "644"):
            logger.error("Не удалось установить разрешения для build.prop. Завершение работы.")
            return False

        # Перезагрузка устройства для применения изменений
        self.adb_manager.reboot_device()

        logger.info("Эмуляция Samsung Galaxy S10 завершена успешно.")
        return True


def main():
    """
    Основная функция скрипта.
    """
    logger.info("Запуск скрипта эмуляции Samsung Galaxy S10...")

    # Инициализация ADBManager
    adb_manager = ADBManager()

    if not adb_manager.is_adb_installed():
        logger.error("ADB не установлен или недоступен. Завершение работы скрипта.")
        sys.exit(1)

    if not adb_manager.device:
        logger.error("Устройство не подключено или подключено несколько устройств. Завершение работы скрипта.")
        sys.exit(1)

    # Инициализация BuildPropManager
    build_prop_manager = BuildPropManager(local_path="build.prop")

    # Инициализация SamsungS10Emulator
    emulator = SamsungS10Emulator(adb_manager, build_prop_manager)

    # Запуск процесса эмуляции
    success = emulator.emulate_samsung_s10()

    if success:
        logger.info("Скрипт выполнен успешно.")
    else:
        logger.error("Скрипт завершился с ошибками.")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.exception(f"Неожиданная ошибка: {e}")
        sys.exit(1)
