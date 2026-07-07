@echo off
chcp 65001 >nul
cd /d "%~dp0"

where python >nul 2>&1
if errorlevel 1 (
    echo Python не найден. Установите Python 3.10+ с https://www.python.org/downloads/
    echo При установке отметьте "Add Python to PATH".
    pause
    exit /b 1
)

echo Установка зависимостей...
python -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo Не удалось установить зависимости.
    pause
    exit /b 1
)

echo Запуск VLauncher...
where pythonw >nul 2>&1
if errorlevel 1 (
    start "" python main.py
) else (
    start "" pythonw main.py
)
exit /b 0
