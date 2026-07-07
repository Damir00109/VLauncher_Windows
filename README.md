# VLauncher

Игровой лаунчер для сервера **Underworld Minecraft**.

## Быстрый старт

### Windows

1. Установите [Python 3.10+](https://www.python.org/downloads/) (при установке включите **Add Python to PATH**).
2. Запустите **`start.bat`** — зависимости установятся автоматически.

### macOS / Linux

1. Python 3.10+ и **git** в системе (`brew install python@3.12 git` на Mac).
2. В терминале:

```bash
chmod +x start.sh
./start.sh
```

3. Войдите под аккаунтом, выберите сборку и нажмите **ИГРАТЬ**.

При первом запуске лаунчер скачает Minecraft, моды и нужные файлы — это может занять несколько минут.

## Возможности

- Вход в аккаунт с автоматическим восстановлением сессии
- Выбор сборки с сервера и установка/обновление файлов
- Настройка RAM для каждой сборки
- Установка текстур и шейдеров через встроенный Packs-Selector
- Журнал событий в **Настройки → Консоль**

## Структура папок

| Папка | Назначение |
|-------|------------|
| `.minecraft/` | Общие файлы Minecraft |
| `instances/` | Файлы каждой сборки (сейвы, моды, текстуры) |
| `submodules/` | Packs-Selector (скачивается автоматически) |
| `tools/` | Portable Git (скачивается автоматически) |

## Ручной запуск

**Windows:**

```bat
pip install -r requirements.txt
python main.py
```

**macOS / Linux:**

```bash
python3 -m venv .venv
.venv/bin/python3 -m pip install -r requirements.txt
.venv/bin/python3 main.py
```
