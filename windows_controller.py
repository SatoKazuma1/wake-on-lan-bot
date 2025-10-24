#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Модуль для управления Windows системой
"""

import os
import time
from typing import List, Dict

import dotenv
from dotenv import load_dotenv
load_dotenv()

import psutil
import win32con
import win32gui
import win32process
screen_password = os.getenv("UNLOCK_PASSWORD")
import pyautogui
pyautogui.FAILSAFE = False

class WindowsSystemController:
    """Расширенный класс для управления Windows системой"""
    
    @staticmethod
    def shutdown(force: bool = False) -> str:
        """Выключение компьютера"""
        try:
            if force:
                os.system("shutdown /s /f /t 0")
            else:
                os.system("shutdown /s /t 0")
            return "✅ Команда выключения отправлена"
        except Exception as e:
            return f"❌ Ошибка выключения: {str(e)}"
    
    @staticmethod
    def restart(force: bool = False) -> str:
        """Перезагрузка компьютера"""
        try:
            if force:
                os.system("shutdown /r /f /t 0")
            else:
                os.system("shutdown /r /t 0")
            return "✅ Команда перезагрузки отправлена"
        except Exception as e:
            return f"❌ Ошибка перезагрузки: {str(e)}"
    
    @staticmethod
    def sleep() -> str:
        """Переход в режим сна"""
        try:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
            return "✅ Компьютер переходит в режим сна"
        except Exception as e:
            return f"❌ Ошибка перехода в сон: {str(e)}"
    
    @staticmethod
    def hibernate() -> str:
        """Переход в режим гибернации"""
        try:
            os.system("shutdown /h")
            return "✅ Компьютер переходит в режим гибернации"
        except Exception as e:
            return f"❌ Ошибка гибернации: {str(e)}"
    
    @staticmethod
    def lock_screen() -> str:
        """Блокировка экрана"""
        try:
            os.system("rundll32.exe user32.dll,LockWorkStation")
            return "✅ Экран заблокирован"
        except Exception as e:
            return f"❌ Ошибка блокировки: {str(e)}"

    # @staticmethod
    # def unlock_screen() -> str:
    #     """Разблокировка экрана"""
    #     #todo функция разблокировки
    #     try:
    #         pyautogui.press("space")
    #         time.sleep(0.5)
    #         pyautogui.write(screen_password)
    #         pyautogui.press("enter")
    #
    #         return "✅ Экран заблокирован"
    #     except Exception as e:
    #         return f"❌ Ошибка разблокировки: {str(e)}"
    """
    К сожалению на python не представляется возможным
    """
    
    @staticmethod
    def get_system_info() -> Dict[str, str]:
        """Получение информации о системе"""
        try:
            info = {
                "Компьютер": os.environ.get('COMPUTERNAME', 'Неизвестно'),
                "Пользователь": os.environ.get('USERNAME', 'Неизвестно'),
                "ОС": f"{os.name} {os.sys.platform}",
                "Время работы": WindowsSystemController._get_uptime(),
                "CPU": f"{psutil.cpu_count()} ядер, загрузка: {psutil.cpu_percent()}%",
                "RAM": WindowsSystemController._get_memory_info(),
                "Диск": WindowsSystemController._get_disk_info()
            }
            return info
        except Exception as e:
            return {"Ошибка": str(e)}
    
    @staticmethod
    def _get_uptime() -> str:
        """Получение времени работы системы"""
        try:
            uptime_seconds = time.time() - psutil.boot_time()
            hours, remainder = divmod(int(uptime_seconds), 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours}ч {minutes}м {seconds}с"
        except:
            return "Неизвестно"
    
    @staticmethod
    def _get_memory_info() -> str:
        """Получение информации о памяти"""
        try:
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024**3)
            used_gb = memory.used / (1024**3)
            return f"{used_gb:.1f}GB / {total_gb:.1f}GB ({memory.percent}%)"
        except:
            return "Неизвестно"
    
    @staticmethod
    def _get_disk_info() -> str:
        """Получение информации о диске"""
        try:
            disk = psutil.disk_usage('C:')
            total_gb = disk.total / (1024**3)
            used_gb = disk.used / (1024**3)
            return f"{used_gb:.1f}GB / {total_gb:.1f}GB ({disk.percent}%)"
        except:
            return "Неизвестно"

class WindowsProcessManager:
    """Класс для управления процессами Windows"""
    
    @staticmethod
    def get_running_processes(limit: int = 20) -> List[Dict[str, str]]:
        """Получение списка запущенных процессов"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['name'] and proc_info['name'] != '':
                        processes.append({
                            'pid': str(proc_info['pid']),
                            'name': proc_info['name'][:30],  # Ограничиваем длину имени
                            'cpu': f"{proc_info['cpu_percent']:.1f}%",
                            'memory': f"{proc_info['memory_percent']:.1f}%"
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Сортируем по использованию CPU
            processes.sort(key=lambda x: float(x['cpu'].replace('%', '')), reverse=True)
            return processes[:limit]
        
        except Exception as e:
            return [{'error': str(e)}]
    
    @staticmethod
    def kill_process(pid: int) -> str:
        """Завершение процесса по PID"""
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            process.terminate()
            return f"✅ Процесс {process_name} (PID: {pid}) завершен"
        except psutil.NoSuchProcess:
            return f"❌ Процесс с PID {pid} не найден"
        except psutil.AccessDenied:
            return f"❌ Нет прав для завершения процесса PID {pid}"
        except Exception as e:
            return f"❌ Ошибка завершения процесса: {str(e)}"
    
    @staticmethod
    def kill_process_by_name(name: str) -> str:
        """Завершение процесса по имени"""
        try:
            killed_count = 0
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if proc.info['name'].lower() == name.lower():
                        proc.terminate()
                        killed_count += 1
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if killed_count > 0:
                return f"✅ Завершено {killed_count} процесс(ов) с именем {name}"
            else:
                return f"❌ Процессы с именем {name} не найдены"
        
        except Exception as e:
            return f"❌ Ошибка завершения процесса: {str(e)}"

class WindowsWindowManager:
    """Класс для управления окнами Windows"""
    
    @staticmethod
    def get_visible_windows() -> List[Dict[str, str]]:
        """Получение списка видимых окон"""
        windows = []
        
        def enum_windows_callback(hwnd, windows_list):
            if win32gui.IsWindowVisible(hwnd):
                window_text = win32gui.GetWindowText(hwnd)
                if window_text:  # Только окна с заголовком
                    try:
                        # Получаем информацию о процессе
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        process = psutil.Process(pid)
                        
                        windows_list.append({
                            'hwnd': str(hwnd),
                            'title': window_text[:50],  # Ограничиваем длину заголовка
                            'process': process.name(),
                            'pid': str(pid)
                        })
                    except:
                        windows_list.append({
                            'hwnd': str(hwnd),
                            'title': window_text[:50],
                            'process': 'Unknown',
                            'pid': 'Unknown'
                        })
        
        try:
            win32gui.EnumWindows(enum_windows_callback, windows)
            return windows[:20]  # Ограничиваем количество окон
        except Exception as e:
            return [{'error': str(e)}]
    
    @staticmethod
    def activate_window(hwnd: int) -> str:
        """Активация окна по handle"""
        try:
            hwnd = int(hwnd)
            if win32gui.IsWindow(hwnd):
                # Восстанавливаем окно если оно свернуто
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                # Делаем окно активным
                win32gui.SetForegroundWindow(hwnd)
                window_title = win32gui.GetWindowText(hwnd)
                return f"✅ Окно '{window_title}' активировано"
            else:
                return "❌ Окно не найдено"
        except Exception as e:
            return f"❌ Ошибка активации окна: {str(e)}"
    
    @staticmethod
    def minimize_window(hwnd: int) -> str:
        """Сворачивание окна"""
        try:
            hwnd = int(hwnd)
            if win32gui.IsWindow(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                window_title = win32gui.GetWindowText(hwnd)
                return f"✅ Окно '{window_title}' свернуто"
            else:
                return "❌ Окно не найдено"
        except Exception as e:
            return f"❌ Ошибка сворачивания окна: {str(e)}"
    
    @staticmethod
    def close_window(hwnd: int) -> str:
        """Закрытие окна"""
        try:
            hwnd = int(hwnd)
            if win32gui.IsWindow(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                return f"✅ Команда закрытия отправлена окну '{window_title}'"
            else:
                return "❌ Окно не найдено"
        except Exception as e:
            return f"❌ Ошибка закрытия окна: {str(e)}"

class WindowsVolumeController:
    """Класс для управления звуком"""
    
    @staticmethod
    def set_volume(level: int) -> str:
        """Установка уровня громкости (0-100)"""
        try:
            if 0 <= level <= 100:
                # Используем nircmd для управления звуком
                os.system(f"nircmd.exe setsysvolume {int(level * 655.35)}")
                return f"✅ Громкость установлена на {level}%"
            else:
                return "❌ Уровень громкости должен быть от 0 до 100"
        except Exception as e:
            return f"❌ Ошибка установки громкости: {str(e)}"
    
    @staticmethod
    def mute() -> str:
        """Отключение звука"""
        try:
            os.system("nircmd.exe mutesysvolume 1")
            return "✅ Звук отключен"
        except Exception as e:
            return f"❌ Ошибка отключения звука: {str(e)}"
    
    @staticmethod
    def unmute() -> str:
        """Включение звука"""
        try:
            os.system("nircmd.exe mutesysvolume 0")
            return "✅ Звук включен"
        except Exception as e:
            return f"❌ Ошибка включения звука: {str(e)}"

