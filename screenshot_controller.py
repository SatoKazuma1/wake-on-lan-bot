"""
Модуль для создания скриншотов Windows
"""

import io
from datetime import datetime
from typing import Optional, Tuple

import pyautogui
import win32con
import win32gui
import win32ui
from PIL import Image, ImageDraw, ImageFont

class WindowsScreenshot:
    """Класс для создания скриншотов в Windows"""
    
    def __init__(self):
        # Отключаем защиту от случайного движения мыши в pyautogui
        pyautogui.FAILSAFE = False
    
    def take_full_screenshot(self, save_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Создает скриншот всего экрана

        Возвращает:
            Tuple[bool, str, Optional[str]]: (успех, сообщение, путь к файлу)
        """
        try:
            # Создаем скриншот
            screenshot = pyautogui.screenshot()
            
            # Добавляем информацию о времени
            screenshot_with_info = self._add_timestamp(screenshot)
            
            # Определяем путь для сохранения
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                save_path = f"screenshot_full_{timestamp}.png"
            
            # Сохраняем файл
            screenshot_with_info.save(save_path, "PNG")
            
            return True, f"✅ Скриншот сохранен: {save_path}", save_path
            
        except Exception as e:
            return False, f"❌ Ошибка создания скриншота: {str(e)}", None
    
    def take_window_screenshot(self, window_title: Optional[str] = None, save_path: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """
        Создает скриншот активного окна или окна по заголовку
        
        Аргументы:
            window_title: Заголовок окна (если None, то активное окно)
            save_path: Путь для сохранения
            
        Возвращает:
            Tuple[bool, str, Optional[str]]: (успех, сообщение, путь к файлу)
        """
        try:
            if window_title:
                # Ищем окно по заголовку
                hwnd = win32gui.FindWindow(None, window_title)
                if not hwnd:
                    return False, f"❌ Окно с заголовком '{window_title}' не найдено", None
            else:
                # Получаем активное окно
                hwnd = win32gui.GetForegroundWindow()
                if not hwnd:
                    return False, "❌ Активное окно не найдено", None
            
            # Получаем размеры окна
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x1, y1 = rect
            width = x1 - x
            height = y1 - y
            
            if width <= 0 or height <= 0:
                return False, "❌ Некорректные размеры окна", None
            
            # Создаем скриншот окна
            screenshot = self._capture_window(hwnd, x, y, width, height)
            
            if not screenshot:
                return False, "❌ Не удалось создать скриншот окна", None
            
            # Добавляем информацию
            window_title_actual = win32gui.GetWindowText(hwnd)
            screenshot_with_info = self._add_window_info(screenshot, window_title_actual)
            
            # Определяем путь для сохранения
            if not save_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_title = "".join(c for c in window_title_actual if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
                save_path = f"screenshot_window_{safe_title}_{timestamp}.png"
            
            # Сохраняем файл
            screenshot_with_info.save(save_path, "PNG")
            
            return True, f"✅ Скриншот окна '{window_title_actual}' сохранен: {save_path}", save_path
            
        except Exception as e:
            return False, f"❌ Ошибка создания скриншота окна: {str(e)}", None
    
    def _capture_window(self, hwnd: int, x: int, y: int, width: int, height: int) -> Optional[Image.Image]:
        """Создает скриншот конкретного окна"""
        try:
            # Получаем контекст устройства окна
            hwndDC = win32gui.GetWindowDC(hwnd)
            mfcDC = win32ui.CreateDCFromHandle(hwndDC)
            saveDC = mfcDC.CreateCompatibleDC()
            
            # Создаем bitmap
            saveBitMap = win32ui.CreateBitmap()
            saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
            saveDC.SelectObject(saveBitMap)
            
            # Копируем содержимое окна
            result = saveDC.BitBlt((0, 0), (width, height), mfcDC, (0, 0), win32con.SRCCOPY)
            
            if result:
                # Получаем данные bitmap
                bmpinfo = saveBitMap.GetInfo()
                bmpstr = saveBitMap.GetBitmapBits(True)
                
                # Создаем PIL Image
                img = Image.frombuffer(
                    'RGB',
                    (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
                    bmpstr, 'raw', 'BGRX', 0, 1
                )
                
                # Освобождаем ресурсы
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)
                
                return img
            else:
                # Если не удалось скопировать, используем pyautogui
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
                return screenshot
                
        except Exception:
            # В случае ошибки используем pyautogui как fallback
            try:
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
                return screenshot
            except:
                return None
        
        finally:
            # Очищаем ресурсы в любом случае
            try:
                win32gui.DeleteObject(saveBitMap.GetHandle())
                saveDC.DeleteDC()
                mfcDC.DeleteDC()
                win32gui.ReleaseDC(hwnd, hwndDC)
            except:
                pass
    
    def _add_timestamp(self, image: Image.Image) -> Image.Image:
        """Добавляет временную метку на скриншот"""
        try:
            # Создаем копию изображения
            img_with_timestamp = image.copy()
            draw = ImageDraw.Draw(img_with_timestamp)
            
            # Получаем текущее время
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Пытаемся загрузить шрифт
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            
            # Определяем позицию для текста (правый нижний угол)
            text_width, text_height = draw.textsize(timestamp, font=font)
            x = img_with_timestamp.width - text_width - 10
            y = img_with_timestamp.height - text_height - 10
            
            # Рисуем фон для текста
            draw.rectangle([x-5, y-5, x+text_width+5, y+text_height+5], fill=(0, 0, 0, 128))
            
            # Рисуем текст
            draw.text((x, y), timestamp, fill=(255, 255, 255), font=font)
            
            return img_with_timestamp
            
        except Exception:
            # Если не удалось добавить метку, возвращаем оригинал
            return image
    
    def _add_window_info(self, image: Image.Image, window_title: str) -> Image.Image:
        """Добавляет информацию об окне на скриншот"""
        try:
            # Создаем копию изображения
            img_with_info = image.copy()
            draw = ImageDraw.Draw(img_with_info)
            
            # Получаем информацию
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            info_text = f"{window_title} | {timestamp}"
            
            # Пытаемся загрузить шрифт
            try:
                font = ImageFont.truetype("arial.ttf", 14)
            except:
                font = ImageFont.load_default()
            
            # Определяем позицию для текста (верхний левый угол)
            text_width, text_height = draw.textsize(info_text, font=font)
            
            # Рисуем фон для текста
            draw.rectangle([5, 5, text_width+15, text_height+15], fill=(0, 0, 0, 128))
            
            # Рисуем текст
            draw.text((10, 10), info_text, fill=(255, 255, 255), font=font)
            
            return img_with_info
            
        except Exception:
            # Если не удалось добавить информацию, возвращаем оригинал
            return image
    
    def get_screenshot_as_bytes(self, screenshot_type: str = "full", window_title: Optional[str] = None) -> Tuple[bool, str, Optional[bytes]]:
        """
        Создает скриншот и возвращает его как байты для отправки в Telegram
        
        Args:
            screenshot_type: "full" или "window"
            window_title: Заголовок окна (для типа "window")
            
        Returns:
            Tuple[bool, str, Optional[bytes]]: (успех, сообщение, данные изображения)
        """
        try:
            if screenshot_type == "full":
                screenshot = pyautogui.screenshot()
                screenshot_with_info = self._add_timestamp(screenshot)
            else:  # window
                hwnd = None
                if window_title:
                    hwnd = win32gui.FindWindow(None, window_title)
                else:
                    hwnd = win32gui.GetForegroundWindow()
                
                if not hwnd:
                    return False, "❌ Окно не найдено", None
                
                rect = win32gui.GetWindowRect(hwnd)
                x, y, x1, y1 = rect
                width = x1 - x
                height = y1 - y
                
                if width <= 0 or height <= 0:
                    return False, "❌ Некорректные размеры окна", None
                
                screenshot = self._capture_window(hwnd, x, y, width, height)
                if not screenshot:
                    return False, "❌ Не удалось создать скриншот", None
                
                window_title_actual = win32gui.GetWindowText(hwnd)
                screenshot_with_info = self._add_window_info(screenshot, window_title_actual)
            
            # Конвертируем в байты
            img_bytes = io.BytesIO()
            screenshot_with_info.save(img_bytes, format='PNG')
            img_bytes.seek(0)
            
            return True, "✅ Скриншот создан", img_bytes.getvalue()
            
        except Exception as e:
            return False, f"❌ Ошибка создания скриншота: {str(e)}", None

class WindowsScreenRecorder:
    """Класс для записи экрана (базовая функциональность)"""
    
    @staticmethod
    def is_recording_available() -> bool:
        """Проверяет доступность записи экрана"""
        try:
            # Проверяем наличие необходимых библиотек
            import cv2
            return True
        except ImportError:
            return False
    
    @staticmethod
    def get_recording_info() -> str:
        """Возвращает информацию о возможностях записи"""
        if WindowsScreenRecorder.is_recording_available():
            return "✅ Запись экрана доступна (требует установки opencv-python)"
        else:
            return "❌ Для записи экрана установите: pip install opencv-python"

