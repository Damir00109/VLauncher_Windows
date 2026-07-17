@echo off
chcp 65001 >nul
setlocal EnableExtensions
cd /d "%~dp0"

rem Portable Miniforge (conda) → tools\conda
rem Окружение лаунчера → tools\conda\envs\vlauncher
rem Вызов: install-conda.bat [/quiet]

set "QUIET=0"
if /i "%~1"=="/quiet" set "QUIET=1"

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"
set "CONDA_DIR=%ROOT%\tools\conda"
set "ENV_DIR=%CONDA_DIR%\envs\vlauncher"
set "CONDA_EXE=%CONDA_DIR%\Scripts\conda.exe"
set "ENV_PY=%ENV_DIR%\python.exe"
set "INSTALLER=%TEMP%\Miniforge3-Windows-x86_64.exe"
set "URL=https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Windows-x86_64.exe"

echo === VLauncher: установка portable Conda ===
echo.

if exist "%ENV_PY%" (
    echo Окружение уже есть: %ENV_DIR%
    goto :deps
)

if not exist "%CONDA_EXE%" (
    echo Скачивание Miniforge...
    curl.exe -L --fail --retry 3 -o "%INSTALLER%" "%URL%"
    if errorlevel 1 (
        echo curl недоступен, пробуем PowerShell...
        powershell -NoProfile -ExecutionPolicy Bypass -Command ^
            "Invoke-WebRequest -Uri '%URL%' -OutFile '%INSTALLER%'"
        if errorlevel 1 (
            echo Не удалось скачать Miniforge. Проверьте интернет.
            if "%QUIET%"=="0" pause
            exit /b 1
        )
    )

    if not exist "%ROOT%\tools" mkdir "%ROOT%\tools"

    echo Установка в tools\conda (несколько минут, без PATH и ярлыков)...
    start /wait "" "%INSTALLER%" /InstallationType=JustMe /RegisterPython=0 /AddToPath=0 /NoShortcuts=1 /S /D=%CONDA_DIR%
    if errorlevel 1 (
        echo Ошибка установки Miniforge.
        if "%QUIET%"=="0" pause
        exit /b 1
    )

    del /f /q "%INSTALLER%" 2>nul

    if not exist "%CONDA_EXE%" (
        echo Miniforge установлен, но conda.exe не найден: %CONDA_EXE%
        echo Убедитесь, что путь к проекту без пробелов и спецсимволов.
        if "%QUIET%"=="0" pause
        exit /b 1
    )
    echo Miniforge готов: %CONDA_DIR%
)

echo.
echo Создание окружения vlauncher ^(Python 3.12^)...
"%CONDA_EXE%" create -y -p "%ENV_DIR%" python=3.12 pip
if errorlevel 1 (
    echo Не удалось создать окружение.
    if "%QUIET%"=="0" pause
    exit /b 1
)

:deps
echo.
echo Установка зависимостей VLauncher...
"%ENV_PY%" -m pip install --upgrade pip -q
"%ENV_PY%" -m pip install -r "%ROOT%\requirements.txt" -q
if errorlevel 1 (
    echo Не удалось установить зависимости.
    if "%QUIET%"=="0" pause
    exit /b 1
)

echo.
echo Готово.
echo   Conda:     %CONDA_DIR%
echo   Python:    %ENV_PY%
echo   Запуск:    start.bat
echo.
echo Для ручной работы в терминале:
echo   call "%CONDA_DIR%\Scripts\activate.bat" "%ENV_DIR%"
echo.
if "%QUIET%"=="0" pause
exit /b 0
