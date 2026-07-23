@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0"

set "ROOT=%~dp0"
if "%ROOT:~-1%"=="\" set "ROOT=%ROOT:~0,-1%"
set "ENV_PY=%ROOT%\tools\conda\envs\vlauncher\python.exe"
set "NAME=VLauncher"
set "DIST_EXE=%ROOT%\dist\%NAME%.exe"
set "ICON_FILE=%ROOT%\launcher\ui\assets\logo.ico"
if not exist "%ICON_FILE%" if exist "%ROOT%\logo.ico" set "ICON_FILE=%ROOT%\logo.ico"
set "PY="

echo === Build %NAME% (onefile) ===
echo.

if exist "%ENV_PY%" (
    set "PY=%ENV_PY%"
) else (
    where python >nul 2>&1
    if errorlevel 1 (
        echo Python not found.
        echo Run install-conda.bat or install Python 3.10+ into PATH.
        goto :end_fail
    )
    for /f "delims=" %%i in ('where python') do (
        if not defined PY set "PY=%%i"
    )
)

if not defined PY (
    echo Python not found.
    goto :end_fail
)

echo Python: %PY%
echo.

echo [1/3] Installing dependencies and PyInstaller...
"%PY%" -m pip install -r "%ROOT%\requirements.txt" pyinstaller -q
if errorlevel 1 (
    echo Failed to install dependencies.
    goto :end_fail
)

echo [2/3] Running PyInstaller (onefile)...
set "ICON_ARG="
if exist "%ICON_FILE%" set "ICON_ARG=--icon=%ICON_FILE%"

if defined ICON_ARG (
    "%PY%" -m PyInstaller --noconfirm --clean --windowed --onefile --name "%NAME%" --paths "%ROOT%" --collect-all PyQt6 --collect-all minecraft_launcher_lib --collect-all certifi --add-data "%ROOT%\launcher\ui\assets;launcher\ui\assets" --add-data "%ROOT%\launcher\patcher\assets;launcher\patcher\assets" %ICON_ARG% "%ROOT%\main.py"
) else (
    echo WARNING: logo.ico not found, exe will have a default icon.
    "%PY%" -m PyInstaller --noconfirm --clean --windowed --onefile --name "%NAME%" --paths "%ROOT%" --collect-all PyQt6 --collect-all minecraft_launcher_lib --collect-all certifi --add-data "%ROOT%\launcher\ui\assets;launcher\ui\assets" --add-data "%ROOT%\launcher\patcher\assets;launcher\patcher\assets" "%ROOT%\main.py"
)

if errorlevel 1 (
    echo.
    echo Build failed.
    goto :end_fail
)

if not exist "%DIST_EXE%" (
    echo Build output not found: %DIST_EXE%
    goto :end_fail
)

echo [3/3] Done.
echo.
echo   Single EXE: %DIST_EXE%
echo.
echo Notes:
echo   - You can copy just this one file.
echo   - First launch unpacks to a temp folder (slower start).
echo   - For Packs-Selector keep Python nearby:
echo       tools\conda\envs\vlauncher  (install-conda.bat)
echo     or python in PATH.
echo   - .minecraft, instances, session.json are created next to the exe.
echo.
pause
exit /b 0

:end_fail
echo.
pause
exit /b 1
