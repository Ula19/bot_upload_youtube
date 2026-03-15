# bot_4_youtube — Telegram-бот для скачивания видео с YouTube

Бот для скачивания видео (MP4) и аудио (MP3) с YouTube через Telegram.

## Возможности

- 🎬 Скачивание видео в 360p / 720p
- 🎵 Скачивание аудио (MP3)
- 📱 Поддержка YouTube Shorts
- 🚀 **Файлы до 2 ГБ** через Local Bot API
- 💾 Кэширование file_id для быстрой повторной отправки
- 📢 Обязательная подписка на каналы
- 👨‍💼 Админ-панель: статистика, каналы, массовая рассылка
- 🌐 Мультиязычность: 🇷🇺 Русский, 🇺🇿 O'zbek, 🇬🇧 English
- 🛡 Rate limiting (5 запросов/минуту)

## Деплой (Docker)

```bash
# 1. Клонировать и настроить
cp .env.example .env
# заполнить .env

# 2. Запустить (бот + Local Bot API + PostgreSQL)
docker compose up -d

# 3. Проверить логи
docker compose logs -f bot
```

### Сервисы docker-compose

| Сервис | Описание | Порт |
|---|---|---|
| `bot` | Наш бот (aiogram) | — |
| `bot-api` | Local Bot API (файлы до 2 ГБ) | 8081 |
| `postgres` | PostgreSQL 16 | 5432 |

## Локальная разработка

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполнить .env (BOT_API_URL можно не менять)
python -m bot.main
```

## Переменные окружения (.env)

| Переменная | Описание | Обязательно |
|---|---|---|
| `BOT_TOKEN` | Токен от @BotFather | ✅ |
| `DB_HOST` | Хост PostgreSQL | ✅ |
| `DB_PORT` | Порт PostgreSQL (5432) | ✅ |
| `DB_NAME` | Имя БД | ✅ |
| `DB_USER` | Юзер PostgreSQL | ✅ |
| `DB_PASSWORD` | Пароль PostgreSQL | ✅ |
| `API_ID` | Telegram API ID (my.telegram.org) | ✅* |
| `API_HASH` | Telegram API Hash | ✅* |
| `ADMIN_IDS` | ID админов через запятую | ❌ |
| `BOT_API_URL` | URL Local Bot API | ❌** |

\* Нужны для Local Bot API сервера.
\** По умолчанию `https://api.telegram.org` (лимит 50 МБ). При деплое через docker-compose — `http://bot-api:8081` (лимит 2 ГБ).

## Системные зависимости

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian (в Docker уже установлен)
sudo apt install ffmpeg
```

## Зависимости (Python)

- `aiogram` 3.26 — Telegram Bot API
- `SQLAlchemy` 2.0 + `asyncpg` — PostgreSQL ORM
- `yt-dlp` — скачивание YouTube видео
- `pydantic-settings` — конфигурация из .env
- `alembic` — миграции БД
- `aiofiles` — асинхронная работа с файлами
- `uvloop` — ускорение asyncio в 2-4x (macOS/Linux)

## Структура проекта

```
bot/
├── main.py          — точка входа
├── config.py        — настройки из .env
├── i18n.py          — переводы (ru/uz/en)
├── database/        — модели и CRUD
├── handlers/        — обработчики сообщений
├── middlewares/      — подписка + rate limit
├── keyboards/       — inline-клавиатуры
├── services/        — скачивание YouTube (yt-dlp)
└── utils/           — валидация URL
```
