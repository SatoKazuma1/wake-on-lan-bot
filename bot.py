"""
Telegram Bot для удаленного управления Windows компьютером
"""

import logging
import os
from typing import Dict, Any

from dotenv import load_dotenv
from telegram import Update, ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters

# Импортируем модули управления Windows
try:
    from windows_controller import WindowsSystemController, WindowsProcessManager, WindowsWindowManager, \
        WindowsVolumeController
    from screenshot_controller import WindowsScreenshot, WindowsScreenRecorder

    WINDOWS_MODULES_AVAILABLE = True
except ImportError:
    # Если модули недоступны (например, не на Windows), создаем заглушки
    WINDOWS_MODULES_AVAILABLE = False


    class WindowsSystemController:
        @staticmethod
        def shutdown(): return "❌ Функция недоступна на данной платформе"

        @staticmethod
        def restart(): return "❌ Функция недоступна на данной платформе"

        @staticmethod
        def sleep(): return "❌ Функция недоступна на данной платформе"

        @staticmethod
        def lock_screen(): return "❌ Функция недоступна на данной платформе"

        @staticmethod
        def get_system_info(): return {"Ошибка": "Модули Windows недоступны"}


    class WindowsProcessManager:
        @staticmethod
        def get_running_processes(): return [{"error": "Модули Windows недоступны"}]

        @staticmethod
        def kill_process(pid): return "❌ Функция недоступна на данной платформе"


    class WindowsWindowManager:
        @staticmethod
        def get_visible_windows(): return [{"error": "Модули Windows недоступны"}]

        @staticmethod
        def activate_window(hwnd): return "❌ Функция недоступна на данной платформе"


    class WindowsScreenshot:
        def get_screenshot_as_bytes(self, screenshot_type, window_title=None):
            return False, "❌ Функция недоступна на данной платформе", None

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Получаем токен бота и пароль из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
UNLOCK_PASSWORD = os.getenv('UNLOCK_PASSWORD')
AUTHORIZED_USER_ID = os.getenv('AUTHORIZED_USER_ID')

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в файле .env")

# Словарь для хранения состояний ожидания подтверждения
pending_confirmations: Dict[int, Dict[str, Any]] = {}


def get_main_keyboard():
    """Создает основную клавиатуру бота"""
    keyboard = [
        ['💻 Управление питанием', '🔒 Блокировка экрана'],
        ['📸 Скриншот', '🪟 Управление окнами'],
        ['📋 Процессы', '🔊 Звук'],
        ['ℹ️ Информация о системе', '❓ Помощь']
    ]

    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


def get_power_keyboard():
    """Создает клавиатуру управления питанием"""
    keyboard = [
        [InlineKeyboardButton("🔴 Выключить", callback_data="power_shutdown")],
        [InlineKeyboardButton("🔄 Перезагрузить", callback_data="power_restart")],
        [InlineKeyboardButton("😴 Режим сна", callback_data="power_sleep")],
        [InlineKeyboardButton("🛌 Гибернация", callback_data="power_hibernate")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_screen_keyboard():
    """Создает клавиатуру управления экраном"""
    keyboard = [
        [InlineKeyboardButton("🔒 Заблокировать", callback_data="screen_lock")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_screenshot_keyboard():
    """Создает клавиатуру для скриншотов"""
    keyboard = [
        [InlineKeyboardButton("🖥️ Весь экран", callback_data="screenshot_full")],
        [InlineKeyboardButton("🪟 Активное окно", callback_data="screenshot_window")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_processes_keyboard():
    """Создает клавиатуру для управления процессами"""
    keyboard = [
        [InlineKeyboardButton("📋 Список процессов", callback_data="processes_list")],
        [InlineKeyboardButton("🔍 Поиск процесса", callback_data="processes_search")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_windows_keyboard():
    """Создает клавиатуру для управления окнами"""
    keyboard = [
        [InlineKeyboardButton("🪟 Список окон", callback_data="windows_list")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_sound_keyboard():
    """Создает клавиатуру для управления звуком"""
    keyboard = [
        [InlineKeyboardButton("🔇 Выключить", callback_data="sound_mute")],
        [InlineKeyboardButton("🔊 Включить", callback_data="sound_unmute")],
        [InlineKeyboardButton("🔉 Громкость 50%", callback_data="sound_50")],
        [InlineKeyboardButton("🔊 Громкость 100%", callback_data="sound_100")],
        [InlineKeyboardButton("◀️ Назад", callback_data="back_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard(action: str):
    """Создает клавиатуру подтверждения действия"""
    keyboard = [
        [InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{action}")],
        [InlineKeyboardButton("❌ Отменить", callback_data="cancel_action")]
    ]
    return InlineKeyboardMarkup(keyboard)


def is_authorized(user_id: int) -> bool:
    """Проверяет авторизацию пользователя"""
    if AUTHORIZED_USER_ID:
        return str(user_id) == AUTHORIZED_USER_ID

    return True


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return

    welcome_text = (
        "🤖 Добро пожаловать в бот управления Windows!\n\n"
        "Доступные функции:\n"
        "💻 Управление питанием - выключение, перезагрузка, сон\n"
        "🔒 Блокировка экрана\n"
        "📸 Создание скриншотов\n"
        "🪟 Управление окнами\n"
        "📋 Просмотр процессов\n"
        "🔊 Управление звуком\n"
        "ℹ️ Информация о системе\n"
        "\nВыберите нужную функцию из меню ниже:"
    )

    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard()
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик текстовых сообщений"""
    user_id = update.effective_user.id

    if not is_authorized(user_id):
        await update.message.reply_text("❌ У вас нет доступа к этому боту.")
        return

    text = update.message.text

    if text == '💻 Управление питанием':
        await update.message.reply_text(
            "⚡ Выберите действие:",
            reply_markup=get_power_keyboard()
        )

    elif text == '🔒 Блокировка экрана':
        await update.message.reply_text(
            "🔐 Управление экраном:",
            reply_markup=get_screen_keyboard()
        )

    elif text == '📸 Скриншот':
        await update.message.reply_text(
            "📷 Выберите тип скриншота:",
            reply_markup=get_screenshot_keyboard()
        )

    elif text == '🪟 Управление окнами':
        await update.message.reply_text(
            "🪟 Управление окнами:",
            reply_markup=get_windows_keyboard()
        )

    elif text == '📋 Процессы':
        await update.message.reply_text(
            "📋 Управление процессами:",
            reply_markup=get_processes_keyboard()
        )

    elif text == '🔊 Звук':
        await update.message.reply_text(
            "🔊 Управление звуком:",
            reply_markup=get_sound_keyboard()
        )

    elif text == 'ℹ️ Информация о системе':
        await handle_system_info(update, context)

    elif text == '❓ Помощь':
        await show_help(update, context)

    else:
        await update.message.reply_text(
            "❓ Неизвестная команда. Используйте кнопки меню.",
            reply_markup=get_main_keyboard()
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик callback запросов от inline кнопок"""
    query = update.callback_query
    await query.answer()

    if not is_authorized(query.from_user.id):
        await query.edit_message_text("❌ У вас нет доступа к этому боту.")
        return

    data = query.data
    user_id = query.from_user.id

    # Обработка подтверждений
    if data.startswith("confirm_"):
        action = data.replace("confirm_", "")
        await execute_confirmed_action(query, action)
        return

    elif data == "cancel_action":
        if user_id in pending_confirmations:
            del pending_confirmations[user_id]
        await query.edit_message_text(
            "❌ Действие отменено.",
            reply_markup=None
        )
        return

    elif data == "back_main":
        await query.edit_message_text(
            "🏠 Главное меню. Выберите функцию:",
            reply_markup=None
        )
        return

    # Обработка действий, требующих подтверждения
    critical_actions = ["power_shutdown", "power_restart", "power_sleep", "power_hibernate", "screen_lock"]

    if data in critical_actions:
        action_names = {
            "power_shutdown": "выключение компьютера",
            "power_restart": "перезагрузку компьютера",
            "power_sleep": "переход в режим сна",
            "power_hibernate": "переход в гибернацию",
            "screen_lock": "блокировку экрана",
        }

        pending_confirmations[user_id] = {"action": data}

        await query.edit_message_text(
            f"⚠️ Вы уверены, что хотите выполнить {action_names[data]}?",
            reply_markup=get_confirmation_keyboard(data)
        )
        return

    # Обработка других действий
    elif data == "screenshot_full":
        await handle_screenshot(query, "full")

    elif data == "screenshot_window":
        await handle_screenshot(query, "window")

    elif data == "processes_list":
        await handle_processes_list(query)

    elif data == "windows_list":
        await handle_windows_list(query)

    elif data == "sound_mute":
        result = WindowsVolumeController.mute()
        await query.edit_message_text(f"🔇 {result}")

    elif data == "sound_unmute":
        result = WindowsVolumeController.unmute()
        await query.edit_message_text(f"🔊 {result}")

    elif data == "sound_50":
        result = WindowsVolumeController.set_volume(50)
        await query.edit_message_text(f"🔉 {result}")

    elif data == "sound_100":
        result = WindowsVolumeController.set_volume(100)
        await query.edit_message_text(f"🔊 {result}")

    # Обработка активации окон
    elif data.startswith("activate_window_"):
        hwnd = data.replace("activate_window_", "")
        result = WindowsWindowManager.activate_window(hwnd)
        await query.edit_message_text(f"🪟 {result}")

    # Обработка завершения процессов
    elif data.startswith("kill_process_"):
        pid = data.replace("kill_process_", "")
        result = WindowsProcessManager.kill_process(int(pid))
        await query.edit_message_text(f"⚠️ {result}")

    # Обработка скриншотов окон
    elif data.startswith("screenshot_window_"):
        hwnd = data.replace("screenshot_window_", "")
        await handle_screenshot_by_hwnd(query, hwnd)


async def execute_confirmed_action(query, action: str) -> None:
    """Выполняет подтвержденное действие"""
    user_id = query.from_user.id

    if user_id in pending_confirmations:
        del pending_confirmations[user_id]

    try:
        if action == "power_shutdown":
            result = WindowsSystemController.shutdown()
            await query.edit_message_text(f"🔴 {result}")

        elif action == "power_restart":
            result = WindowsSystemController.restart()
            await query.edit_message_text(f"🔄 {result}")

        elif action == "power_sleep":
            result = WindowsSystemController.sleep()
            await query.edit_message_text(f"😴 {result}")

        elif action == "power_hibernate":
            result = WindowsSystemController.hibernate()
            await query.edit_message_text(f"🛌 {result}")

        elif action == "screen_lock":
            result = WindowsSystemController.lock_screen()
            await query.edit_message_text(f"🔒 {result}")

        # elif action == "screen_unlock":
        #     result = WindowsSystemController.unlock_screen()
        #     await query.edit_message_text(f"🔓 {result}")

    except Exception as e:
        logger.error(f"Ошибка выполнения действия {action}: {e}")
        await query.edit_message_text(f"❌ Ошибка выполнения действия: {str(e)}")


async def handle_system_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка запроса информации о системе"""
    try:
        info = WindowsSystemController.get_system_info()

        info_text = "ℹ️ **Информация о системе:**\n\n"
        for key, value in info.items():
            info_text += f"**{key}:** {value}\n"

        await update.message.reply_text(info_text, parse_mode='Markdown')

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка получения информации: {str(e)}")


async def handle_processes_list(query) -> None:
    """Обработка запроса списка процессов"""
    try:
        processes = WindowsProcessManager.get_running_processes(15)

        if processes and 'error' not in processes[0]:
            text = "📋 **Активные процессы:**\n\n"
            for i, proc in enumerate(processes, 1):
                text += f"{i}. **{proc['name']}** (PID: {proc['pid']})\n"
                text += f"   CPU: {proc['cpu']}, RAM: {proc['memory']}\n\n"

            # Создаем кнопки для завершения процессов
            keyboard = []
            for proc in processes[:5]:  # Показываем кнопки только для первых 5 процессов
                keyboard.append([InlineKeyboardButton(
                    f"❌ Завершить {proc['name'][:15]}",
                    callback_data=f"kill_process_{proc['pid']}"
                )])
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main")])

            await query.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("❌ Ошибка получения списка процессов")

    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")


async def handle_windows_list(query) -> None:
    """Обработка запроса списка окон"""
    try:
        windows = WindowsWindowManager.get_visible_windows()

        if windows and 'error' not in windows[0]:
            text = "🪟 **Активные окна:**\n\n"
            for i, window in enumerate(windows, 1):
                text += f"{i}. **{window['title']}**\n"
                text += f"   Процесс: {window['process']} (PID: {window['pid']})\n\n"

            # Создаем кнопки для управления окнами
            keyboard = []
            for window in windows[:4]:  # Показываем кнопки только для первых 4 окон
                keyboard.append([
                    InlineKeyboardButton(
                        f"🎯 {window['title'][:15]}",
                        callback_data=f"activate_window_{window['hwnd']}"
                    ),
                    InlineKeyboardButton(
                        f"📸 Скриншот",
                        callback_data=f"screenshot_window_{window['hwnd']}"
                    )
                ])
            keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_main")])

            await query.edit_message_text(
                text,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.edit_message_text("❌ Ошибка получения списка окон")

    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}")


async def handle_screenshot_by_hwnd(query, hwnd: str) -> None:
    """Создает скриншот окна по его handle"""
    try:
        await query.edit_message_text("📸 Создаю скриншот окна...")

        # Получаем заголовок окна
        import win32gui
        try:
            window_title = win32gui.GetWindowText(int(hwnd))
        except:
            window_title = "Неизвестное окно"

        screenshot_controller = WindowsScreenshot()
        success, message, img_bytes = screenshot_controller.get_screenshot_as_bytes("window", window_title)

        if success and img_bytes:
            await query.message.reply_photo(
                photo=img_bytes,
                caption=f"📸 Скриншот окна: {window_title}\n{message}"
            )
            await query.edit_message_text("✅ Скриншот окна отправлен!")
        else:
            await query.edit_message_text(f"❌ {message}")

    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка создания скриншота: {str(e)}")


async def handle_screenshot(query, screenshot_type: str) -> None:
    """Обработка создания скриншотов"""
    try:
        await query.edit_message_text("📸 Создаю скриншот...")

        # Создаем объект для работы со скриншотами
        screenshot_controller = WindowsScreenshot()

        # Создаем скриншот
        success, message, img_bytes = screenshot_controller.get_screenshot_as_bytes(screenshot_type)

        if success and img_bytes:
            # Отправляем скриншот
            await query.message.reply_photo(
                photo=img_bytes,
                caption=f"📸 Скриншот ({screenshot_type})\n{message}"
            )
            await query.edit_message_text("✅ Скриншот отправлен!")
        else:
            await query.edit_message_text(f"❌ {message}")

    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка создания скриншота: {str(e)}")


async def handle_screenshot_window_by_title(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                            window_title: str) -> None:
    """Создает скриншот конкретного окна по заголовку"""
    try:
        await update.message.reply_text("📸 Создаю скриншот окна...")

        screenshot_controller = WindowsScreenshot()
        success, message, img_bytes = screenshot_controller.get_screenshot_as_bytes("window", window_title)

        if success and img_bytes:
            await update.message.reply_photo(
                photo=img_bytes,
                caption=f"📸 Скриншот окна: {window_title}\n{message}"
            )
        else:
            await update.message.reply_text(f"❌ {message}")

    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает справку по боту"""
    help_text = (
        "🤖 Справка по боту управления Windows\n\n"
        "📋 Доступные функции:\n\n"
        "💻 Управление питанием:\n"
        "• Выключение компьютера\n"
        "• Перезагрузка компьютера\n"
        "• Переход в режим сна\n"
        "• Пробуждение от сна\n\n"
        "🔒 Управление экраном:\n"
        "• Блокировка экрана\n"
        "📸 Скриншоты:\n"
        "• Скриншот всего экрана\n"
        "• Скриншот активного окна\n\n"
        "🪟 Управление окнами:\n"
        "• Список активных окон\n"
        "• Активация окна\n\n"
        "📋 Процессы:\n"
        "• Список активных процессов\n\n"
        "⚠️ Критические действия требуют подтверждения."
    )

    await update.message.reply_text(help_text)


def main():
    """Главная функция запуска бота"""
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN не найден в переменных окружения!")
        return

    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(handle_callback))

    # Запускаем бота
    logger.info("Запуск бота...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()