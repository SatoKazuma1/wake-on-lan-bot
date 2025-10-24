@echo off

REM Переходим в рабочую папку на диске Z:
cd /d "Z:\soft\wake-on-lan"

REM Проверка, что папка существует и переход удался
if %errorlevel% neq 0 (
    REM Если не удалось, можно записать ошибку в лог-файл для отладки
    echo %date% %time% - Failed to change directory to Z:\soft\wake-on-lan >> C:\Scripts\bot_error.log
    exit /b 1
)

REM Активируем виртуальное окружение
call .venv\Scripts\activate

REM Последовательно запускаем Python-скрипты в фоновом режиме.
REM Используем pythonw.exe, чтобы не создавались окна консоли.
REM start /b гарантирует, что они запустятся как фоновые процессы.

start "WiFi Fixer" /b pythonw wifi_fixer.py
REM Добавим небольшую паузу, если wifi_fixer'у нужно время для работы
timeout /t 5 /nobreak > nul

start "WakeBot" /b pythonw bot.py

exit /b 0