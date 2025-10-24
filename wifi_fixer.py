"""Модуль для починки wi-fi на моем компе
    Так как китайцы заскамили меня на материнскую плату за 20к рублей от Gygabite,
мне приходится при каждом 2-3 включении компьютера перезагружать драйвер для беспроводного адаптера.
Примечательно что на arch такой проблемы никогда не было.

    Также этот модуль закрывает клиент wireguard если он открыт, так как при аварийном завершении
работы он будет мешать при следующем старте.

    В целом модуль состоит из хардкода и мягко говоря написан на коленке чисто для себя. Если у кого-то из знакомых
появится схожая проблема вынесу все значения в конфиг и улучшу логирование.
"""

import subprocess
import time
import socket
import psutil

WIFI_ADAPTER_NAME = 'Беспроводная сеть' # У меня он так называется

"""Лишняя работа, kill_process() справляется самостоятельно"""
# def check_process(process_name) -> bool | None:
#     try:
#         for proc in psutil.process_iter(['name']):
#             if proc.info['name'].lower() == process_name.lower():
#                 return True
#     except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
#         return False


def kill_process(process_name) -> bool | None:
    found_processes = []
    for proc in psutil.process_iter(['name', 'pid']):
        try:
            if proc.info['name'].lower() == process_name.lower():
                found_processes.append(proc)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    if not found_processes:
        return False
    try:
        for proc in found_processes:
            try:
                proc.terminate()
                time.sleep(1)
                if proc.is_running():
                    proc.kill()
                    proc.wait(timeout=3)
            except psutil.TimeoutExpired:
                pass
    except psutil.AccessDenied:
        pass
    return True

def check_internet_connection(host="8.8.8.8", port=53, timeout=5):
    """
    Проверяет наличие интернет-соединения, пытаясь подключиться к указанному хосту
    По умолчанию проверяет соединение с dns сервером Google
    """
    try:
        # Попытка создать сокет-соединение с хостом и портом
        socket.create_connection((host, port), timeout)
        return True
    except OSError:
        return False

def toggle_wifi_adapter(adapter_name, max_retries=10):
    """
    Отключает и включает wi-fi адаптер, повторяя попытки, если интернет не появляется
    """
    if check_internet_connection():
        return True
    for attempt in range(1, max_retries + 1):
        print(f"\nПопытка {attempt}/{max_retries}:")
        print(f"Попытка отключить адаптер: {adapter_name}")
        try:
            # Отключение адаптера
            subprocess.run(['netsh', 'interface', 'set', 'interface', adapter_name, 'disable'], check=True)
            print(f"Адаптер {adapter_name} отключен. Ожидание 3 секунды...")
            time.sleep(3) # Даем время на полное отключение

            # Включение адаптера
            print(f"Попытка включить адаптер: {adapter_name}")
            subprocess.run(['netsh', 'interface', 'set', 'interface', adapter_name, 'enable'], check=True)
            print(f"Адаптер {adapter_name} включен. Ожидание 30 секунд для появления соединения...") # TODO вынести время ожидания в параметр функции и выводить в этой строке
            time.sleep(30) # Ждем 30 секунд для появления соединения

            if check_internet_connection():
                print("Интернет-соединение установлено успешно!")
                return True
            else:
                print("Интернет-соединение не обнаружено после включения адаптера.")
                if attempt < max_retries:
                    print("Повторная попытка...")
                else:
                    print("Достигнуто максимальное количество попыток. Не удалось установить интернет-соединение.")
                    return False

        except subprocess.CalledProcessError as subprocess_error:
            print(f"Ошибка при выполнении команды netsh: {subprocess_error}")
            print("Убедитесь, что скрипт запущен от имени администратора и имя адаптера указано верно.")
            return False # Выход при критической ошибке
        except Exception as unknown_error:
            print(f"Произошла непредвиденная ошибка: {unknown_error}")
            return False # Выход при непредвиденной ошибке
    return False # Должно быть достигнуто, если все попытки исчерпаны

if __name__ == "__main__":
    try:
        # if check_process('wireguard.exe'):
        kill_process('wireguard.exe')
        print("Запуск скрипта для исправления Wi-Fi соединения...")
        if toggle_wifi_adapter(WIFI_ADAPTER_NAME):
            print("Скрипт завершен успешно: интернет-соединение восстановлено.")
        else:
            print("Скрипт завершен: не удалось восстановить интернет-соединение.")
    except Exception as wifi_error:
        with open('/logs/wifi_log.txt', 'a+') as f:
            f.write(f"Ошибка wifi_fixer: {wifi_error}\n")