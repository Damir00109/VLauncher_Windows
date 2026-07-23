# VLauncher

Игровой лаунчер для сервера **Underworld Minecraft**.

Windows-релизы: [Damir00109/VLauncher_Windows](https://github.com/Damir00109/VLauncher_Windows).

## Быстрый старт

### Windows (из исходников)

1. Запустите **`start.bat`** — при первом запуске поставит portable Conda в `tools/conda`.
2. Альтернатива со системным Python: **`start-old.bat`** (нужен [Python 3.10+](https://www.python.org/downloads/) в PATH).

### Windows (готовый exe)

1. Скачайте `VLauncher.exe` из [Releases](https://github.com/Damir00109/VLauncher_Windows/releases).
2. Запустите. Данные по умолчанию: `%APPDATA%\.mcvanilla`.

Сборка exe: **`build.bat`** → `dist\VLauncher.exe`.

## Данные и настройки

По умолчанию лаунчер хранит всё в **`%APPDATA%\.mcvanilla`**:

| Путь | Назначение |
|------|------------|
| `.minecraft/` | Клиент, libraries, assets |
| `instances/` | Сборки (сейвы, моды, текстуры) |
| `submodules/` | Packs-Selector |
| `tools/` | Portable Git и пр. |
| `session.json` | Сессия входа |
| `profile_settings.json` | RAM и опциональные моды |
| `.vlauncher_prefs.json` | Настройки лаунчера |

Путь можно сменить в **Настройки → Папка данных**.

Указатель на выбранный путь хранится в `%APPDATA%\VLauncher\prefs.json` (чтобы путь можно было сменить).

## Обновления

Лаунчер сам проверяет [GitHub Releases](https://github.com/Damir00109/VLauncher_Windows/releases) при старте и по кнопке в настройках.

Как выложить обновление:

1. Поднимите `APP_VERSION` в `launcher/config.py` (например `0.2.0`).
2. Соберите `build.bat`.
3. В репозитории `VLauncher_Windows` создайте Release с тегом **`v0.2.0`**.
4. Прикрепите asset **`VLauncher.exe`**.

## Возможности

- Вход в аккаунт с восстановлением сессии
- Выбор сборки, установка и обновление файлов
- Настройка RAM для каждой сборки
- Текстуры и шейдеры через Packs-Selector
- Своя папка данных и проверка обновлений с GitHub

## Ручной запуск

```bat
pip install -r requirements.txt
python main.py
```
