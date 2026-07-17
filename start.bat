@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "ENV_PY=%ROOT%\tools\conda\envs\vlauncher\python.exe"
set "ENV_PYW=%ROOT%\tools\conda\envs\vlauncher\pythonw.exe"

if not exist "%ENV_PY%" (
    echo Первый запуск: установка portable Conda...
    echo.
    call "%~dp0install-conda.bat" /quiet
    if errorlevel 1 (
        echo Не удалось установить Conda.
        pause
        exit /b 1
    )
    if not exist "%ENV_PY%" (
        echo Окружение Conda не найдено после установки.
        pause
        exit /b 1
    )
)

echo Установка зависимостей...
"%ENV_PY%" -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo Не удалось установить зависимости.
    pause
    exit /b 1
)

echo Запуск VLauncher...
if exist "%ENV_PYW%" (
    start "" "%ENV_PYW%" main.py
) else (
    start "" "%ENV_PY%" main.py
)
exit /b 0
