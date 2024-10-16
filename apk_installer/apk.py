#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
F-Droid APK Installer

Этот скрипт автоматически скачивает и устанавливает APK-файлы из репозитория F-Droid на подключённое устройство или эмулятор Android с помощью ADB.

Функциональность:
1. Загрузка и парсинг index.xml из F-Droid.
2. Извлечение актуальных URL-адресов APK-файлов для указанных пакетов.
3. Асинхронное скачивание APK-файлов с верификацией их целостности.
4. Установка APK-файлов на устройство через ADB с обработкой ошибок.
5. Подробное логирование всех операций.

Предварительные требования:
- Python 3.8 или выше.
- Установленные Python-пакеты: aiohttp, aiofiles, lxml, tqdm.
- Установленный ADB и добавленный в переменную окружения PATH.

Установка необходимых Python-пакетов:
    pip install aiohttp aiofiles lxml tqdm

Использование:
    python3 fdroid_installer.py

Автор: ChatGPT o1
Лицензия: GPL-3.0-only
"""

import os
import sys
import asyncio
import aiohttp
import aiofiles
import subprocess
import logging
import hashlib
from datetime import datetime
from lxml import etree
from tqdm import tqdm
from typing import List, Dict
from concurrent.futures import ThreadPoolExecutor
import shutil

# Конфигурация
LOG_DIR = "./logs"
APK_DIR = "./fdroid_apks"
FDROID_INDEX_URL = "https://f-droid.org/repo/index.xml"
MAX_DOWNLOAD_CONCURRENT = 5  # Максимальное количество одновременных загрузок
MAX_INSTALL_CONCURRENT = 3   # Максимальное количество одновременных установок

# Список пакетов для установки
PACKAGES = [
    "org.fossify.clock",
    "org.fossify.keyboard",
    "org.fdroid.fdroid",
    "org.fossify.contacts",
    "org.fossify.gallery",
    "org.fossify.filemanager",
    "org.fossify.calendar",
    "com.termux",
    "org.fossify.messages",
 #   "com.cpuid.cpu_z",
    "org.fossify.phone",
    "com.kgurgul.cpuinfo",
    "com.termux.api",
    "org.telegram.messenger",
    
]


class Package:
    """
    Класс, представляющий приложение для установки из F-Droid.
    """
    def __init__(self, package_id: str, version: str, versioncode: int, apkname: str, hash_value: str, apk_url: str):
        self.package_id = package_id
        self.version = version
        self.versioncode = versioncode
        self.apkname = apkname
        self.hash_value = hash_value
        self.apk_url = apk_url
        self.local_path = os.path.join(APK_DIR, self.apkname)


class FdroidInstaller:
    """
    Класс для автоматической установки APK-файлов из F-Droid с использованием ADB.
    """
    def __init__(self, packages: List[str]):
        self.packages = packages
        self.executor = ThreadPoolExecutor(max_workers=MAX_INSTALL_CONCURRENT)

        # Настройка логирования
        os.makedirs(LOG_DIR, exist_ok=True)
        log_filename = datetime.now().strftime("install_fdroid_apps_%Y%m%d_%H%M%S.log")
        log_path = os.path.join(LOG_DIR, log_filename)

        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.info("Логирование запущено.")
        logging.info(f"Логи сохраняются в: {log_path}")

    async def run(self):
        """
        Основной метод для выполнения всех шагов установки.
        """
        try:
            await self.check_dependencies()
            device = await self.get_connected_device()
            index_path = await self.download_index_xml()
            package_infos = self.parse_index_xml(index_path)
            if not package_infos:
                logging.error("Не удалось найти ни одного пакета в index.xml.")
                sys.exit(1)
            await self.download_and_install_packages(package_infos)
            logging.info("Все указанные пакеты были обработаны.")
        except Exception as e:
            logging.error(f"Неизвестная ошибка: {e}")
        finally:
            self.executor.shutdown(wait=True)

    async def check_dependencies(self):
        """
        Проверка наличия необходимых утилит и Python-пакетов.
        """
        logging.info("Проверка зависимостей...")
        # Проверка наличия ADB
        if not shutil.which("adb"):
            logging.error("ADB не установлен или не добавлен в PATH. Пожалуйста, установите ADB.")
            sys.exit(1)
        # Проверка наличия Python-пакетов
        try:
            import aiohttp
            import aiofiles
            import lxml
            import tqdm
        except ImportError as e:
            logging.error(f"Необходимый Python-пакет не установлен: {e}")
            sys.exit(1)
        logging.info("Все зависимости установлены.")

    async def get_connected_device(self) -> str:
        """
        Получение идентификатора подключённого устройства через ADB.
        """
        logging.info("Получение подключённого устройства через ADB...")
        try:
            process = await asyncio.create_subprocess_exec(
                'adb', 'devices',
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode != 0:
                logging.error(f"Ошибка при выполнении ADB: {stderr.decode().strip()}")
                sys.exit(1)
            lines = stdout.decode().strip().split('\n')
            devices = [line.split()[0] for line in lines[1:] if line.strip() and len(line.split()) > 1 and line.split()[1] == 'device']
            if not devices:
                logging.error("Нет подключённых устройств. Пожалуйста, подключите устройство или запустите эмулятор.")
                sys.exit(1)
            elif len(devices) > 1:
                logging.error("Обнаружено несколько устройств. Пожалуйста, уточните устройство с помощью ADB.")
                for device in devices:
                    logging.error(f" - {device}")
                sys.exit(1)
            device = devices[0]
            logging.info(f"Подключено устройство: {device}")
            return device
        except Exception as e:
            logging.error(f"Ошибка при получении устройства через ADB: {e}")
            sys.exit(1)

    async def download_index_xml(self) -> str:
        """
        Скачивание index.xml из репозитория F-Droid.
        """
        logging.info("Скачивание F-Droid index.xml...")
        try:
            os.makedirs(APK_DIR, exist_ok=True)
            async with aiohttp.ClientSession() as session:
                async with session.get(FDROID_INDEX_URL) as response:
                    if response.status != 200:
                        logging.error(f"Не удалось скачать index.xml. Статус код: {response.status}")
                        sys.exit(1)
                    index_content = await response.text()
            index_path = os.path.join(APK_DIR, "index.xml")
            async with aiofiles.open(index_path, 'w', encoding='utf-8') as f:
                await f.write(index_content)
            logging.info("index.xml успешно скачан.")
            return index_path
        except Exception as e:
            logging.error(f"Ошибка при скачивании index.xml: {e}")
            sys.exit(1)

    def parse_index_xml(self, index_path: str) -> Dict[str, Package]:
        """
        Парсинг index.xml и извлечение информации о пакетах.

        :param index_path: Путь к скачанному index.xml
        :return: Словарь с информацией о пакетах
        """
        logging.info("Парсинг index.xml...")
        try:
            with open(index_path, 'rb') as f:
                tree = etree.parse(f)
            root = tree.getroot()
            package_dict = {}
            for application in root.findall('application'):
                app_id = application.find('id').text
                if app_id in self.packages:
                    for pkg in application.findall('package'):
                        versioncode_text = pkg.find('versioncode').text
                        try:
                            versioncode = int(versioncode_text)
                        except ValueError:
                            logging.warning(f"Неверный versioncode '{versioncode_text}' для пакета {app_id}. Пропуск.")
                            continue
                        if (app_id not in package_dict) or (versioncode > package_dict[app_id].versioncode):
                            apkname = pkg.find('apkname').text
                            hash_value = pkg.find('hash').text
                            apk_url = pkg.find('apkname').text  # Правильный путь
                            version = pkg.find('version').text
                            package = Package(
                                package_id=app_id,
                                version=version,
                                versioncode=versioncode,
                                apkname=apkname,
                                hash_value=hash_value,
                                apk_url=apk_url
                            )
                            package_dict[app_id] = package
            if not package_dict:
                logging.warning("Пакеты из списка не найдены в index.xml.")
            else:
                logging.info(f"Найдено {len(package_dict)} пакетов для установки.")
            return package_dict
        except etree.XMLSyntaxError as e:
            logging.error(f"Ошибка синтаксиса XML: {e}")
            sys.exit(1)
        except Exception as e:
            logging.error(f"Ошибка при парсинге index.xml: {e}")
            sys.exit(1)

    async def download_and_install_packages(self, package_dict: Dict[str, Package]):
        """
        Асинхронное скачивание и установка пакетов.

        :param package_dict: Словарь с информацией о пакетах
        """
        logging.info("Начало процесса скачивания и установки пакетов...")
        tasks = []
        semaphore = asyncio.Semaphore(MAX_DOWNLOAD_CONCURRENT)

        for package_id, package in package_dict.items():
            tasks.append(self.process_package(package, semaphore))

        await asyncio.gather(*tasks)

    async def process_package(self, package: Package, semaphore: asyncio.Semaphore):
        """
        Обработка одного пакета: скачивание и установка.

        :param package: Объект Package
        :param semaphore: Семафор для ограничения количества одновременных загрузок
        """
        async with semaphore:
            logging.info(f"Обработка пакета: {package.package_id}")
            success = await self.download_apk(package)
            if success:
                await self.install_apk(package)
            else:
                logging.error(f"Пропуск установки пакета {package.package_id} из-за ошибки при скачивании.")
            logging.info("----------------------------------------")

    async def download_apk(self, package: Package) -> bool:
        """
        Скачивание APK-файла с верификацией хэш-суммы.

        :param package: Объект Package
        :return: True, если скачивание и верификация успешны, иначе False
        """
        try:
            if os.path.exists(package.local_path):
                logging.info(f"APK для пакета {package.package_id} уже скачан: {package.local_path}")
                if self.verify_apk_hash(package.local_path, package.hash_value):
                    logging.info(f"APK для пакета {package.package_id} прошёл верификацию.")
                    return True
                else:
                    logging.warning(f"APK для пакета {package.package_id} не прошёл верификацию. Повторная загрузка.")
                    os.remove(package.local_path)

            # Используем один из зеркал для скачивания
            mirror_urls = [
                "https://f-droid.org/repo",
                "https://mirror.cyberbits.eu/fdroid/repo",
                "https://mirror.fcix.net/fdroid/repo",
                "https://mirror.kumi.systems/fdroid/repo",
                "https://mirror.level66.network/fdroid/repo",
                "https://mirror.ossplanet.net/fdroid/repo",
                "https://mirrors.dotsrc.org/fdroid/repo",
                "https://opencolo.mm.fcix.net/fdroid/repo",
                "https://plug-mirror.rcac.purdue.edu/fdroid/repo",
                "https://mirror.init7.net/fdroid/repo",
                "https://mirror.freedif.org/fdroid/repo",
                "https://de.freedif.org/fdroid/repo"
            ]

            # Попробуем скачать с первого доступного зеркала
            apk_url_full = None
            for mirror in mirror_urls:
                url = f"{mirror}/{package.apk_url}"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.head(url) as head_resp:
                            if head_resp.status == 200:
                                apk_url_full = url
                                break
                except:
                    continue  # Пробуем следующее зеркало

            if not apk_url_full:
                logging.error(f"Не удалось найти рабочее зеркало для скачивания APK пакета {package.package_id}.")
                return False

            async with aiohttp.ClientSession() as session:
                async with session.get(apk_url_full) as response:
                    if response.status != 200:
                        logging.error(f"Не удалось скачать APK для пакета {package.package_id}. Статус код: {response.status}")
                        return False
                    total_size = int(response.headers.get('content-length', 0))
                    progress_bar = tqdm(
                        desc=f"Скачивание {package.apkname}",
                        total=total_size,
                        unit='iB',
                        unit_scale=True,
                        unit_divisor=1024,
                        leave=False
                    )
                    async with aiofiles.open(package.local_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(1024):
                            if chunk:
                                await f.write(chunk)
                                progress_bar.update(len(chunk))
                    progress_bar.close()

            if self.verify_apk_hash(package.local_path, package.hash_value):
                logging.info(f"APK для пакета {package.package_id} успешно скачан и прошёл верификацию.")
                return True
            else:
                logging.error(f"APK для пакета {package.package_id} не прошёл верификацию.")
                if os.path.exists(package.local_path):
                    os.remove(package.local_path)
                return False
        except Exception as e:
            logging.error(f"Ошибка при скачивании APK для пакета {package.package_id}: {e}")
            return False

    def verify_apk_hash(self, apk_path: str, expected_hash: str) -> bool:
        """
        Проверка хэш-суммы APK-файла.

        :param apk_path: Путь к APK-файлу
        :param expected_hash: Ожидаемая хэш-сумма (SHA256)
        :return: True, если хэш совпадает, иначе False
        """
        try:
            sha256 = hashlib.sha256()
            with open(apk_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            calculated_hash = sha256.hexdigest()
            if calculated_hash.lower() == expected_hash.lower():
                return True
            else:
                logging.error(f"Хэш-сумма APK-файла {apk_path} не совпадает. Ожидалось: {expected_hash}, Получено: {calculated_hash}")
                return False
        except Exception as e:
            logging.error(f"Ошибка при проверке хэш-суммы APK-файла {apk_path}: {e}")
            return False

    async def install_apk(self, package: Package):
        """
        Установка APK-файла на устройство через ADB.

        :param package: Объект Package
        """
        try:
            logging.info(f"Установка APK для пакета {package.package_id}: {package.local_path}")
            process = await asyncio.create_subprocess_exec(
                'adb', 'install', '-r', '-d', package.local_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            if process.returncode == 0:
                logging.info(f"Пакет {package.package_id} успешно установлен.")
                # Удаление APK после установки (опционально)
                # os.remove(package.local_path)
                # logging.info(f"APK-файл для пакета {package.package_id} удалён после установки.")
            else:
                stderr_decoded = stderr.decode().strip()
                logging.error(f"Ошибка при установке пакета {package.package_id}: {stderr_decoded}")
        except Exception as e:
            logging.error(f"Неизвестная ошибка при установке пакета {package.package_id}: {e}")


if __name__ == "__main__":
    installer = FdroidInstaller(PACKAGES)
    try:
        asyncio.run(installer.run())
    except KeyboardInterrupt:
        logging.info("Процесс установки прерван пользователем.")
        sys.exit(0)
