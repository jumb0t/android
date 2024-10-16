#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import logging
import sys
import os
from datetime import datetime
from colorama import init, Fore, Style
from jinja2 import Environment, FileSystemLoader, select_autoescape

# Инициализация colorama
init(autoreset=True)

# Конфигурация логгирования
LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'
LOG_FILE = 'adb_system_info.log'

logging.basicConfig(level=logging.INFO,
                    format=LOG_FORMAT,
                    handlers=[
                        logging.FileHandler(LOG_FILE, encoding='utf-8'),
                        logging.StreamHandler(sys.stdout)
                    ])

class ADBError(Exception):
    """Кастомное исключение для ошибок ADB."""
    pass

class SystemInfoCollector:
    """Класс для сбора информации о системе через ADB."""

    def __init__(self, device):
        self.device = device

    def run_adb_command(self, command):
        """Выполнение команды adb и возврат результата."""
        try:
            logging.debug(f"Выполнение команды для устройства {self.device}: adb {command}")
            result = subprocess.run(['adb', '-s', self.device] + command.split(),
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    text=True,
                                    check=True)
            logging.debug(f"Результат команды для устройства {self.device}: {result.stdout.strip()}")
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            logging.error(f"Ошибка при выполнении adb команды '{command}' для устройства {self.device}: {e.stderr.strip()}")
            raise ADBError(f"ADB command failed: {command}") from e

    def get_system_properties(self):
        """Получение всех системных свойств устройства."""
        properties = self.run_adb_command('shell getprop')
        prop_dict = {}
        for line in properties.split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                key = key.strip().strip('[]')
                value = value.strip().strip('[]')
                prop_dict[key] = value
        return prop_dict

    def get_build_info(self):
        """Получение информации о сборке системы."""
        build_info = {}
        keys = [
            'ro.build.id',
            'ro.build.display.id',
            'ro.build.version.incremental',
            'ro.build.version.sdk',
            'ro.build.version.release',
            'ro.build.version.codename',
            'ro.build.type',
            'ro.build.user',
            'ro.build.host',
            'ro.build.tags',
            'ro.product.model',
            'ro.product.brand',
            'ro.product.name',
            'ro.product.device',
            'ro.product.board',
            'ro.product.cpu.abi',
            'ro.product.manufacturer',
            'ro.build.fingerprint'
        ]
        for key in keys:
            try:
                value = self.run_adb_command(f'shell getprop {key}')
                build_info[key] = value
            except ADBError:
                build_info[key] = 'N/A'
        return build_info

    def get_hardware_info(self):
        """Получение информации о железе устройства."""
        try:
            cpu_info = self.run_adb_command('shell cat /proc/cpuinfo')
        except ADBError:
            cpu_info = "N/A"
        try:
            memory_info = self.run_adb_command('shell cat /proc/meminfo')
        except ADBError:
            memory_info = "N/A"
        hardware_info = {
            'CPU Info': cpu_info,
            'Memory Info': memory_info
        }
        return hardware_info

    def get_installed_apps(self):
        """Получение списка установленных приложений."""
        try:
            apps = self.run_adb_command('shell pm list packages -f')
            app_list = [app.strip() for app in apps.split('\n') if app.strip()]
            return app_list
        except ADBError:
            return ["N/A"]

    def get_storage_info(self):
        """Получение информации о хранилище устройства."""
        try:
            storage = self.run_adb_command('shell df -h')
            return storage
        except ADBError:
            return "N/A"

    def get_battery_info(self):
        """Получение информации о батарее."""
        try:
            battery = self.run_adb_command('shell dumpsys battery')
            return battery
        except ADBError:
            return "N/A"

    def get_network_interfaces(self):
        """Получение списка сетевых интерфейсов."""
        try:
            interfaces = self.run_adb_command('shell ip addr show')
        except ADBError:
            interfaces = "N/A"
        return interfaces

    def get_ip_addresses(self):
        """Получение IP-адресов устройства."""
        try:
            ip_info = self.run_adb_command('shell ip addr show')
        except ADBError:
            ip_info = "N/A"
        return ip_info

    def get_wifi_info(self):
        """Получение информации о Wi-Fi подключениях."""
        try:
            wifi_info = self.run_adb_command('shell dumpsys wifi')
            return wifi_info
        except ADBError:
            return "N/A"

    def get_system_settings(self):
        """Получение системных настроек."""
        settings = {}
        try:
            settings['System'] = self.run_adb_command('shell settings list system')
        except ADBError:
            settings['System'] = "N/A"
        try:
            settings['Secure'] = self.run_adb_command('shell settings list secure')
        except ADBError:
            settings['Secure'] = "N/A"
        try:
            settings['Global'] = self.run_adb_command('shell settings list global')
        except ADBError:
            settings['Global'] = "N/A"
        return settings

    def get_display_info(self):
        """Получение информации о дисплее."""
        try:
            display_info = self.run_adb_command('shell dumpsys display')
        except ADBError:
            display_info = "N/A"
        return display_info

    def get_sensor_info(self):
        """Получение информации о датчиках."""
        try:
            sensor_info = self.run_adb_command('shell dumpsys sensorservice')
        except ADBError:
            sensor_info = "N/A"
        return sensor_info

    def get_cpu_usage(self):
        """Получение информации об использовании CPU."""
        try:
            cpu_usage = self.run_adb_command('shell dumpsys cpuinfo')
        except ADBError:
            cpu_usage = "N/A"
        return cpu_usage

    def get_memory_usage(self):
        """Получение информации об использовании памяти."""
        try:
            memory_usage = self.run_adb_command('shell dumpsys meminfo')
        except ADBError:
            memory_usage = "N/A"
        return memory_usage

    def get_running_services(self):
        """Получение списка запущенных сервисов."""
        try:
            services = self.run_adb_command('shell service list')
            return services
        except ADBError:
            return "N/A"

    def get_running_processes(self):
        """Получение списка запущенных процессов."""
        try:
            processes = self.run_adb_command('shell ps -A')
            return processes
        except ADBError:
            return "N/A"

    def get_device_identifiers(self):
        """Получение идентификаторов устройства."""
        identifiers = {}
        # Android ID
        try:
            android_id = self.run_adb_command('shell settings get secure android_id')
            identifiers['Android ID'] = android_id
        except ADBError:
            identifiers['Android ID'] = 'N/A'

        # Serial Number
        try:
            serial_number = self.run_adb_command('shell getprop ro.serialno')
            identifiers['Serial Number'] = serial_number
        except ADBError:
            identifiers['Serial Number'] = 'N/A'

        # IMEI
        try:
            # Метод 1: Использование telephony
            imei = self.run_adb_command('shell dumpsys telephony.registry | grep mImei')
            if "mImei" in imei:
                imei = imei.split("=")[-1].strip()
                identifiers['IMEI'] = imei
            else:
                raise ADBError("IMEI не найден в telephony.registry")
        except ADBError:
            logging.warning(f"Не удалось получить IMEI через dumpsys telephony.registry для устройства {self.device}. Попробуем другой метод.")
            try:
                # Метод 2: Использование getprop
                imei = self.run_adb_command('shell getprop gsm.imei')
                if imei:
                    identifiers['IMEI'] = imei
                else:
                    raise ADBError("IMEI не найден через getprop gsm.imei")
            except ADBError:
                logging.error(f"Не удалось получить IMEI для устройства {self.device}.")
                identifiers['IMEI'] = 'N/A'

        # MAC-адрес Wi-Fi
        try:
            mac_wifi_interface = self.run_adb_command('shell getprop wifi.interface')
            if mac_wifi_interface and mac_wifi_interface != '':
                mac_wifi_address = self.run_adb_command(f'shell cat /sys/class/net/{mac_wifi_interface}/address')
                identifiers['MAC Address (WiFi)'] = mac_wifi_address.upper()
            else:
                raise ADBError("WiFi interface не найден через getprop wifi.interface")
        except ADBError:
            identifiers['MAC Address (WiFi)'] = 'N/A'

        # MAC-адрес Bluetooth
        try:
            mac_bt = self.run_adb_command('shell getprop bluetooth.bdaddr')
            if mac_bt and mac_bt != '':
                identifiers['MAC Address (Bluetooth)'] = mac_bt.upper()
            else:
                # Альтернативный метод: через getprop bluetooth
                mac_bt = self.run_adb_command('shell getprop bluetooth.address')
                if mac_bt and mac_bt != '':
                    identifiers['MAC Address (Bluetooth)'] = mac_bt.upper()
                else:
                    raise ADBError("Bluetooth MAC не найден через getprop")
        except ADBError:
            identifiers['MAC Address (Bluetooth)'] = 'N/A'

        return identifiers

    def get_introduction(self):
        """Получение введения с общей информацией о устройстве."""
        introduction = {}
        try:
            introduction['Device Name'] = self.run_adb_command('shell getprop ro.product.model')
        except ADBError:
            introduction['Device Name'] = "N/A"

        try:
            introduction['Manufacturer'] = self.run_adb_command('shell getprop ro.product.manufacturer')
        except ADBError:
            introduction['Manufacturer'] = "N/A"

        try:
            introduction['Android Version'] = self.run_adb_command('shell getprop ro.build.version.release')
        except ADBError:
            introduction['Android Version'] = "N/A"

        try:
            introduction['SDK Version'] = self.run_adb_command('shell getprop ro.build.version.sdk')
        except ADBError:
            introduction['SDK Version'] = "N/A"

        try:
            introduction['Build Fingerprint'] = self.run_adb_command('shell getprop ro.build.fingerprint')
        except ADBError:
            introduction['Build Fingerprint'] = "N/A"

        return introduction

    # Дополнительные методы для сбора расширенной информации

    def get_camera_info(self):
        """Получение информации о камерах устройства."""
        try:
            camera_info = self.run_adb_command('shell dumpsys media.camera')
        except ADBError:
            camera_info = "N/A"
        return camera_info

    def get_bluetooth_info(self):
        """Получение информации о Bluetooth устройства."""
        try:
            bluetooth_manager = self.run_adb_command('shell dumpsys bluetooth_manager')
        except ADBError:
            bluetooth_manager = "N/A"
        try:
            bluetooth_adapter = self.run_adb_command('shell dumpsys bluetooth_adapter')
        except ADBError:
            bluetooth_adapter = "N/A"
        return {
            'Bluetooth Manager': bluetooth_manager,
            'Bluetooth Adapter': bluetooth_adapter
        }

    def get_security_settings(self):
        """Получение информации о настройках безопасности устройства."""
        try:
            security_info = self.run_adb_command('shell dumpsys devicepolicy')
        except ADBError:
            security_info = "N/A"
        return security_info

    def get_nfc_info(self):
        """Получение информации о NFC устройства."""
        try:
            nfc_info = self.run_adb_command('shell dumpsys nfc')
        except ADBError:
            nfc_info = "N/A"
        return nfc_info

    def get_usb_config(self):
        """Получение информации о конфигурации USB устройства."""
        try:
            usb_info = self.run_adb_command('shell dumpsys usb')
        except ADBError:
            usb_info = "N/A"
        return usb_info

    def get_vpn_info(self):
        """Получение информации о VPN соединениях устройства."""
        try:
            vpn_info = self.run_adb_command('shell dumpsys vpn')
        except ADBError:
            vpn_info = "N/A"
        return vpn_info

    def get_graphics_info(self):
        """Получение информации о графических настройках устройства."""
        try:
            graphics_info = self.run_adb_command('shell dumpsys gfxinfo')
        except ADBError:
            graphics_info = "N/A"
        return graphics_info

    def get_firewall_info(self):
        """Получение информации о фаерволле устройства."""
        try:
            firewall_info = self.run_adb_command('shell iptables -L')
        except ADBError:
            firewall_info = "N/A"
        return firewall_info

    def get_screen_settings(self):
        """Получение разрешения и плотности экрана."""
        try:
            screen_size = self.run_adb_command('shell wm size')
        except ADBError:
            screen_size = "N/A"
        try:
            screen_density = self.run_adb_command('shell wm density')
        except ADBError:
            screen_density = "N/A"
        return {
            'Screen Size': screen_size,
            'Screen Density': screen_density
        }

    def get_sim_info(self):
        """Получение информации о SIM-картах устройства."""
        try:
            sim_info = self.run_adb_command('shell dumpsys telephony.registry')
        except ADBError:
            sim_info = "N/A"
        return sim_info

    def get_usb_details(self):
        """Получение подробной информации о USB подключениях."""
        try:
            usb_details = self.run_adb_command('shell lsusb')
        except ADBError:
            usb_details = "N/A"
        return usb_details

    def collect_all_info(self):
        """Сбор всей доступной информации о системе."""
        info = {}
        try:
            info['Introduction'] = self.get_introduction()
            info['Device Identifiers'] = self.get_device_identifiers()
            info['System Properties'] = self.get_system_properties()
            info['Build Info'] = self.get_build_info()
            info['Hardware Info'] = self.get_hardware_info()
            info['Installed Apps'] = self.get_installed_apps()
            info['Storage Info'] = self.get_storage_info()
            info['Battery Info'] = self.get_battery_info()
            info['Network Interfaces'] = self.get_network_interfaces()
            info['IP Addresses'] = self.get_ip_addresses()
            info['Wi-Fi Info'] = self.get_wifi_info()
            info['System Settings'] = self.get_system_settings()
            info['Display Info'] = self.get_display_info()
            info['Sensor Info'] = self.get_sensor_info()
            info['CPU Usage'] = self.get_cpu_usage()
            info['Memory Usage'] = self.get_memory_usage()
            info['Running Services'] = self.get_running_services()
            info['Running Processes'] = self.get_running_processes()
            # Дополнительные данные
            info['Camera Info'] = self.get_camera_info()
            info['Bluetooth Info'] = self.get_bluetooth_info()
            info['Security Settings'] = self.get_security_settings()
            info['NFC Info'] = self.get_nfc_info()
            info['USB Configuration'] = self.get_usb_config()
            info['VPN Info'] = self.get_vpn_info()
            info['Graphics Info'] = self.get_graphics_info()
            info['Firewall Info'] = self.get_firewall_info()
            info['Screen Settings'] = self.get_screen_settings()
            info['SIM Info'] = self.get_sim_info()
            info['USB Details'] = self.get_usb_details()
            # Логи могут быть объемными, поэтому их можно включить по желанию
            # info['System Logs'] = self.get_dmesg_logs()
            logging.info(f"Сбор информации завершен успешно для устройства {self.device}.")
        except ADBError as e:
            logging.error(f"Ошибка при сборе информации для устройства {self.device}: {e}")
        return info

class ReportGenerator:
    """Класс для генерации и вывода отчета."""

    def __init__(self, info, device_identifier):
        self.info = info
        self.device_identifier = device_identifier
        self.env = Environment(
            loader=FileSystemLoader(searchpath="./"),
            autoescape=select_autoescape(['html', 'xml'])
        )
        self.template = self.get_template()
        # Описание параметров
        self.descriptions = self.get_descriptions()

    def get_descriptions(self):
        """Получение описаний для параметров."""
        descriptions = {
            'Device Name': 'Название модели устройства.',
            'Manufacturer': 'Производитель устройства.',
            'Android Version': 'Версия операционной системы Android.',
            'SDK Version': 'Версия SDK Android.',
            'Build Fingerprint': 'Уникальный идентификатор сборки Android.',
            'Android ID': 'Уникальный идентификатор устройства Android.',
            'Serial Number': 'Серийный номер устройства.',
            'IMEI': 'Международный идентификатор мобильного оборудования.',
            'MAC Address (WiFi)': 'MAC-адрес Wi-Fi интерфейса устройства.',
            'MAC Address (Bluetooth)': 'MAC-адрес Bluetooth интерфейса устройства.',
            'CPU Info': 'Информация о процессоре устройства.',
            'Memory Info': 'Информация о памяти устройства.',
            'Installed Apps': 'Список установленных приложений на устройстве.',
            'Storage Info': 'Информация о доступном и используемом хранилище устройства.',
            'Battery Info': 'Состояние батареи устройства.',
            'Network Interfaces': 'Список сетевых интерфейсов устройства.',
            'IP Addresses': 'IP-адреса, присвоенные устройству.',
            'Wi-Fi Info': 'Информация о состоянии и подключениях Wi-Fi.',
            'System Settings': 'Системные настройки устройства.',
            'Display Info': 'Информация о дисплее устройства.',
            'Sensor Info': 'Информация о датчиках устройства.',
            'CPU Usage': 'Текущая загрузка процессора устройства.',
            'Memory Usage': 'Текущая загрузка памяти устройства.',
            'Running Services': 'Список запущенных сервисов на устройстве.',
            'Running Processes': 'Список запущенных процессов на устройстве.',
            'Camera Info': 'Информация о камерах устройства.',
            'Bluetooth Manager': 'Состояние и настройки менеджера Bluetooth.',
            'Bluetooth Adapter': 'Информация о адаптере Bluetooth.',
            'Security Settings': 'Настройки безопасности устройства.',
            'NFC Info': 'Состояние и настройки NFC.',
            'USB Configuration': 'Конфигурация USB-подключений.',
            'VPN Info': 'Информация о текущих VPN-соединениях.',
            'Graphics Info': 'Информация о графических настройках устройства.',
            'Firewall Info': 'Состояние и правила фаерволла устройства.',
            'Screen Size': 'Разрешение экрана устройства.',
            'Screen Density': 'Плотность пикселей экрана устройства.',
            'SIM Info': 'Информация о SIM-картах устройства.',
            'USB Details': 'Подробная информация о USB-подключениях устройства.',
            # Добавьте больше описаний по мере необходимости
        }
        return descriptions

    def get_template(self):
        """Получение HTML шаблона."""
        template_content = """
        <!DOCTYPE html>
        <html lang="ru">
        <head>
            <meta charset="UTF-8">
            <title>Отчет о Системе Android - {{ device_identifier }}</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f4f4f4; }
                h1 { text-align: center; color: #2c3e50; }
                h2 { color: #2980b9; cursor: pointer; }
                h3 { color: #16a085; }
                pre { background-color: #ecf0f1; padding: 10px; border-radius: 5px; overflow-x: auto; }
                table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                th, td { border: 1px solid #bdc3c7; padding: 8px; text-align: left; }
                th { background-color: #34495e; color: white; }
                tr:nth-child(even) { background-color: #f2f2f2; }
                .section { margin-bottom: 40px; }
                .description { font-size: 0.9em; color: #7f8c8d; margin-bottom: 10px; }
                .toggle-content { display: none; }
                .active .toggle-content { display: block; }
                .toggle-button { background-color: #2980b9; color: white; padding: 10px; border: none; width: 100%; text-align: left; outline: none; font-size: 18px; cursor: pointer; }
                .toggle-button:hover { background-color: #3498db; }
            </style>
            <script>
                function toggleAccordion(event) {
                    var section = event.currentTarget.parentElement;
                    section.classList.toggle('active');
                }
            </script>
        </head>
        <body>
            <h1>Отчет о Системе Android</h1>
            <p><strong>Устройство:</strong> {{ device_identifier }}</p>
            <p><strong>Дата создания отчета:</strong> {{ report_date }}</p>
            <div class="section">
                <button class="toggle-button" onclick="toggleAccordion(event)">Введение</button>
                <div id="introduction" class="toggle-content">
                    <table>
                        <thead>
                            <tr>
                                <th>Параметр</th>
                                <th>Значение</th>
                                <th>Описание</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for key, value in info.Introduction.items() %}
                            <tr>
                                <td>{{ key }}</td>
                                <td>{{ value }}</td>
                                <td>{{ descriptions.get(key, '') }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            {% for section, data in info.items() %}
                {% if section != 'Introduction' %}
                <div class="section">
                    <button class="toggle-button" onclick="toggleAccordion(event)">{{ section }}</button>
                    <div id="{{ loop.index }}" class="toggle-content">
                        {% if section in descriptions %}
                            <p class="description">{{ descriptions[section] }}</p>
                        {% endif %}
                        {% if data is mapping %}
                            <table>
                                <thead>
                                    <tr>
                                        <th>Параметр</th>
                                        <th>Значение</th>
                                        <th>Описание</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for key, value in data.items() %}
                                        <tr>
                                            <td>{{ key }}</td>
                                            <td>{{ value }}</td>
                                            <td>{{ descriptions.get(key, '') }}</td>
                                        </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        {% elif data is iterable and not data is string %}
                            <pre>{{ data | join('\\n') }}</pre>
                        {% else %}
                            <pre>{{ data }}</pre>
                        {% endif %}
                    </div>
                </div>
                {% endif %}
            {% endfor %}
            <script>
                // Разворачиваем введение по умолчанию
                document.getElementById('introduction').style.display = "block";
                // Разворачиваем введение
                var introSection = document.querySelector('.section');
                if (introSection) {
                    introSection.classList.add('active');
                }
            </script>
        </body>
        </html>
        """
        return self.env.from_string(template_content)

    def generate_html_report(self):
        """Генерация HTML отчета."""
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_content = self.template.render(info=self.info, report_date=report_date, descriptions=self.descriptions, device_identifier=self.device_identifier)
        return html_content

    def print_report(self):
        """Вывод отчета в консоль с цветовой подсветкой."""
        for section, data in self.info.items():
            print(f"{Fore.CYAN}{Style.BRIGHT}{section}{Style.RESET_ALL}")
            if isinstance(data, dict):
                for key, value in data.items():
                    desc = self.descriptions.get(key, '')
                    print(f"{Fore.YELLOW}{key}:{Style.RESET_ALL} {value} - {desc}")
            elif isinstance(data, list):
                for item in data:
                    print(f" - {item}")
            else:
                print(f"{data}")
            print("\n")

    def save_html_report(self, filename):
        """Сохранение HTML отчета в файл."""
        try:
            html_content = self.generate_html_report()
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logging.info(f"HTML отчет сохранен в файл: {filename}")
        except IOError as e:
            logging.error(f"Не удалось сохранить HTML отчет в файл: {e}")

    def save_text_report(self, filename):
        """Сохранение текстового отчета в файл."""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                for section, data in self.info.items():
                    f.write(f"{section}\n{'='*len(section)}\n")
                    if isinstance(data, dict):
                        for key, value in data.items():
                            desc = self.descriptions.get(key, '')
                            f.write(f"{key}: {value} - {desc}\n")
                    elif isinstance(data, list):
                        for item in data:
                            f.write(f" - {item}\n")
                    else:
                        f.write(f"{data}\n")
                    f.write("\n")
            logging.info(f"Текстовый отчет сохранен в файл: {filename}")
        except IOError as e:
            logging.error(f"Не удалось сохранить текстовый отчет в файл: {e}")

def get_connected_devices():
    """Получение списка подключенных устройств."""
    try:
        result = subprocess.run(['adb', 'devices'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True,
                                check=True)
        lines = result.stdout.strip().split('\n')
        devices = [line.split()[0] for line in lines[1:] if 'device' in line]
        return devices
    except subprocess.CalledProcessError as e:
        logging.error(f"Ошибка при выполнении adb devices: {e.stderr.strip()}")
        sys.exit(1)

def main():
    """Главная функция скрипта."""
    devices = get_connected_devices()
    if not devices:
        logging.error("Нет подключенных устройств.")
        sys.exit(1)
    elif len(devices) == 1:
        logging.info(f"Найдено устройство: {devices}")
    else:
        logging.info(f"Найдено устройств: {devices}")

    for device in devices:
        try:
            collector = SystemInfoCollector(device)
            system_info = collector.collect_all_info()
            # Используем серийный номер или Android ID для уникального имени файла
            identifiers = system_info.get('Device Identifiers', {})
            serial_number = identifiers.get('Serial Number', device)
            # Удаляем недопустимые символы из имени файла
            serial_number_clean = ''.join(c for c in serial_number if c.isalnum())
            if not serial_number_clean:
                serial_number_clean = device.replace(':', '')
            html_filename = f'reports/system_report_{serial_number_clean}.html'
            text_filename = f'reports/system_report_{serial_number_clean}.txt'
            reporter = ReportGenerator(system_info, serial_number_clean)
            reporter.print_report()
            reporter.save_html_report(html_filename)
            reporter.save_text_report(text_filename)
        except ADBError as e:
            logging.error(f"Ошибка при обработке устройства {device}: {e}")
        except Exception as e:
            logging.exception(f"Неизвестная ошибка при обработке устройства {device}: {e}")

if __name__ == '__main__':
    # Создаем каталог для отчетов, если его нет
    os.makedirs('reports', exist_ok=True)
    main()
