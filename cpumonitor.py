"""
Модуль для создания красивых плотов с графиками использования ресурсов пк
"""
from typing import Any

import matplotlib
# TODO Создать отдельный модуль со сбором статистики о ресурсах пк и записи их в базу данных.
# TODO Второй бот который будет уведомлять об активности пк каждую 1 минуту(примерно),\
#  каждые 30-60 минут присылать график ресурсов.
# TODO Позаботиться о безопасности, обработка случаев

import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import sqlite3, psutil, pynvml, time, datetime
import pandas as pd

pynvml.nvmlInit()
# Функции для получения использования ресурсов пк
def get_cpu_utilization(): return psutil.cpu_percent(interval=1)
def get_ram_utilization(): return psutil.virtual_memory()
handle = pynvml.nvmlDeviceGetHandleByIndex(0)
def get_gpu_utilization(): return pynvml.nvmlDeviceGetUtilizationRates(handle)

# Автоматическая конвертация строк в класс datetime
def convert_timestamp(val): return datetime.datetime.fromisoformat(val.decode())
sqlite3.register_converter("DATETIME", convert_timestamp)

# Инициализация субд sqlite3.
db = sqlite3.connect('CPUmonitor.db', detect_types=sqlite3.PARSE_DECLTYPES)
cursor = db.cursor()
cursor.execute('''
CREATE TABLE IF NOT EXISTS CPUmonitor (
timestamp DATETIME UNIQUE NOT NULL,
cpu_utilization REAL NOT NULL,
gpu_utilization REAL NOT NULL,
vram_utilization REAL NOT NULL,
ram_utilization REAL NOT NULL
)
''')

def insert_utilization() -> None:
    """
    Функция для записи текущего использования
    :return:
        None
    """
    cursor.execute('''
    INSERT INTO CPUmonitor (timestamp, cpu_utilization, gpu_utilization, vram_utilization, ram_utilization)
    VALUES (?, ?, ?, ?, ?)''',
                   (datetime.datetime.now(), get_cpu_utilization(), get_gpu_utilization().gpu, get_gpu_utilization().memory, get_ram_utilization()[2]))

def get_n_writes(n:int=5) -> list[Any] | None:
    """
    Выдает последние n записей из базы данных, отсортированные по времени с конца

    :param n: Количество записей
    :return:
        [(datetime.datetime, float, float, float, float), ...]
        Либо None
    """
    try:
        cursor.execute(f'''SELECT * FROM CPUmonitor ORDER BY timestamp DESC LIMIT ?''', (n,))
        result = cursor.fetchall()
        result.reverse()
        return result
    except Exception as e:
        print(e)

def make_plot(writes_amount:int=5, smoothing:bool=True) -> tuple[Figure, Any]:
    """
    Создает плот с 4 графиками использования ресурсов пк, данные берет из бд.

    :param writes_amount:
        Параметр n передающийся в get_n_writes(), количество последних записей по которым будет построен плот.
    :param smoothing: Переключатель сглаживания.
    :return:
        Кортеж объектов Figure и массив Axes Matplotlib.
    """
    timelist = []
    cpu_util_list = []
    gpu_util_list = []
    ram_util_list = []
    vram_util_list = []
    for row in get_n_writes(writes_amount):
        timelist.append(row[0])
        cpu_util_list.append(row[1])
        gpu_util_list.append(row[2])
        vram_util_list.append(row[3])
        ram_util_list.append(row[4])
    # Сглаживание
    if smoothing:
        window_size = 10
        cpu_series = pd.Series(cpu_util_list)
        gpu_series = pd.Series(gpu_util_list)
        ram_series = pd.Series(ram_util_list)
        vram_series = pd.Series(vram_util_list)

        cpu_util_list = cpu_series.rolling(window=window_size).mean()
        gpu_util_list = gpu_series.rolling(window=window_size).mean()
        ram_util_list = ram_series.rolling(window=window_size).mean()
        vram_util_list = vram_series.rolling(window=window_size).mean()

    fig, axes = plt.subplots(nrows=2, ncols=2, figsize=(12, 8))
    plt.style.use('seaborn-v0_8-whitegrid')

    ax1 = axes[0, 0]
    ax1.plot(timelist, cpu_util_list, color='blue')
    ax1.set_title('CPU Utilization')  # Вместо легенды используем заголовок
    ax1.set_ylabel('Нагрузка, %')
    ax1.set_ylim(0, 100)

    # График 2: GPU Utilization (верхний правый)
    ax2 = axes[0, 1]
    ax2.plot(timelist, gpu_util_list, color='orange')
    ax2.set_title('GPU Utilization')
    ax2.set_ylim(0, 100)

    # График 3: RAM Utilization (нижний левый)
    ax3 = axes[1, 0]
    ax3.plot(timelist, ram_util_list, color='green')
    ax3.set_title('RAM Utilization')
    ax3.set_ylabel('Нагрузка, %')
    ax3.set_xlabel('Время')
    ax3.set_ylim(0, 100)

    # График 4: VRAM Utilization (нижний правый)
    ax4 = axes[1, 1]
    ax4.plot(timelist, vram_util_list, color='red')
    ax4.set_title('VRAM Utilization')
    ax4.set_xlabel('Время')
    ax4.set_ylim(0, 100)
    plt.tight_layout()
    return fig, axes

print(get_n_writes(5))