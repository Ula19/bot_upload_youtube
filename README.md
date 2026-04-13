# bot_4_youtube — Telegram-бот для скачивания видео с YouTube

Бот для скачивания видео и аудио с YouTube через Telegram.
Aiogram 3 + SQLAlchemy + PostgreSQL + yt-dlp + Local Bot API.

## Возможности

- 🎬 Скачивание видео вплоть до 1440p (динамический список качеств с оценкой размера)
- 🎵 Скачивание аудио (m4a)
- 📱 Поддержка YouTube Shorts
- 🚀 **Файлы до 2 ГБ** через Local Bot API
- ⚖️ Балансировка трафика между резидентным SOCKS5-прокси и Cloudflare WARP:
  - `get_info` — всегда через резидентный прокси (полный список качеств)
  - мелкие видео (< 30 МБ) и аудио — через WARP
  - HD-видео — через резидентный прокси
  - fallback-цепочка: `primary → alt → proxy+cookies → proxy+ios/android`
- 🛡 Префлайт-фильтр — качества с оценкой > 2000 МБ не показываются юзеру (защита от лимита Telegram 2 ГБ)
- 💾 Кэш `file_id` в БД — повторные отправки без скачивания
- 📢 Обязательная подписка на каналы (middleware)
- 👨‍💼 Админ-панель: статистика, управление каналами, рассылка (text/photo/video), обновление cookies
- 🚨 Алерты админам при падении источников (proxy/WARP) с throttling и классификацией ошибок
- 🌐 Мультиязычность: 🇷🇺 Русский · 🇺🇿 O'zbek · 🇬🇧 English
- ⏱ Rate limit — 5 запросов/мин на юзера (in-memory, с фоновой очисткой)
- 🧹 Фоновая очистка `/tmp/yt_bot` (файлы старше 30 мин) и протухших записей rate-limit каждые 5 минут
- ⚡ `uvloop` для ускорения asyncio в 2-4 раза

## Деплой (Docker)

```bash
# 1. Склонировать и настроить
cp .env.example .env
# заполнить .env (BOT_TOKEN, API_ID, API_HASH, DB_*, ADMIN_IDS, PROXY_URL)

# 2. Запустить
docker compose up -d --build

# 3. Логи
docker compose logs -f bot
```

### Сервисы docker-compose

| Сервис     | Образ                               | Назначение                                              |
|------------|-------------------------------------|---------------------------------------------------------|
| `bot`      | собирается из `Dockerfile`          | Python-приложение                                       |
| `bot-api`  | `aiogram/telegram-bot-api:latest`   | Local Bot API — файлы до 2 ГБ (порт `8081`)             |
| `postgres` | `postgres:16-alpine`                | База данных (порт `5432`)                               |
| `warp`     | `ghcr.io/mon-ius/docker-warp-socks` | Cloudflare WARP SOCKS5 (порт `9091` внутри сети)        |
| `autoheal` | `willfarrell/autoheal:latest`       | Авто-рестарт unhealthy контейнеров                      |

## Локальная разработка

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполнить .env
python -m bot.main
```

Для локального запуска `bot-api` и `warp` не обязательны (бот будет работать
через обычный Bot API с лимитом 50 МБ и напрямую без WARP).

## Переменные окружения (`.env`)

| Переменная                  | Описание                                                             | Обязательно |
|-----------------------------|----------------------------------------------------------------------|-------------|
| `BOT_TOKEN`                 | Токен от @BotFather                                                  | ✅          |
| `BOT_USERNAME`              | Юзернейм бота без `@` (для рекламной подписи к медиа)                | ✅          |
| `API_ID`, `API_HASH`        | Креды с https://my.telegram.org — **нужны только для Local Bot API** | ✅ (если поднят `bot-api`) |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Параметры PostgreSQL                            | ✅          |
| `ADMIN_IDS`                 | Telegram-ID админов через запятую (получают алерты, имеют доступ к /admin) | ❌    |
| `ADMIN_USERNAME`            | Username админа для контакта в справке                               | ❌          |
| `PROXY_URL`                 | Резидентный SOCKS5 прокси, `socks5://[user:pass@]host:port`          | ❌          |
| `SMALL_VIDEO_THRESHOLD_MB`  | Порог размера для маршрутизации (< порога → WARP, ≥ порога → прокси). Дефолт `30` | ❌ |
| `MAX_QUALITY_SIZE_MB`       | Префлайт-фильтр: качества с оценкой больше не показываются. Дефолт `2000` | ❌    |
| `CACHE_TTL_DAYS`            | TTL кэша `file_id` в БД. Дефолт `1`                                  | ❌          |

**`BOT_API_URL`** задаётся напрямую в `docker-compose.yml`
(`environment.BOT_API_URL=http://bot-api:8081`) — это тех-параметр обвязки,
а не настройка бизнес-логики.

## Структура проекта

```
bot/
├── main.py              — entrypoint, роутеры, мидлвари, фоновая очистка
├── config.py            — pydantic-settings из .env
├── i18n.py              — переводы (ru/uz/en) + detect_language()
├── emojis.py            — премиум-эмодзи (E_ID и E)
├── database/
│   ├── __init__.py      — engine + async_session
│   ├── models.py        — User / Channel / Download
│   └── crud.py          — все запросы к БД
├── handlers/
│   ├── start.py         — /start, главное меню, смена языка, профиль, проверка подписки
│   ├── download.py      — приём URL, выбор формата/качества, скачивание, алерты админам
│   ├── admin.py         — /admin: статистика, каналы, рассылка
│   └── cookies.py       — /update_cookies для админов
├── middlewares/
│   ├── subscription.py  — обязательная подписка на каналы
│   └── rate_limit.py    — 5 запросов/мин + фоновая очистка
├── keyboards/
│   ├── inline.py        — пользовательские клавиатуры
│   └── admin.py         — админские клавиатуры
├── services/
│   └── youtube.py       — yt-dlp, fallback-цепочка, classify_error()
└── utils/
    ├── commands.py      — персональные и глобальные меню команд Telegram
    └── helpers.py       — валидация и нормализация YouTube URL
```

## Docker-образ

`python:3.12-slim` + `ffmpeg` (конвертация/склейка) + `deno` (JS-рантайм для
решения YouTube n-challenge → нужен для 720p+ DASH-форматов).

## Python-зависимости

- `aiogram==3.26.0` — Telegram Bot API
- `SQLAlchemy==2.0.38` + `asyncpg==0.30.0` — PostgreSQL async ORM
- `yt-dlp>=2025.3.31` — скачивание YouTube
- `pydantic-settings==2.8.1` — конфигурация из `.env`
- `alembic==1.14.1` — миграции БД (пока не используется, таблицы создаются через `create_all()`)
- `aiofiles==24.1.0` — асинхронная работа с файлами
- `pysocks==1.7.1` — SOCKS5-клиент для прокси
- `uvloop==0.22.1` — ускорение asyncio

## Команды бота

| Команда          | Доступ   | Описание                                   |
|------------------|----------|--------------------------------------------|
| `/start`         | Все      | Запуск бота, приветствие, главное меню     |
| `/menu`          | Все      | Главное меню                               |
| `/profile`       | Все      | Профиль юзера (ID, счётчик скачиваний)     |
| `/help`          | Все      | Справка                                    |
| `/language`      | Все      | Смена языка                                |
| `/admin`         | Админы   | Админ-панель                               |
| `/update_cookies`| Админы   | Загрузка свежих `cookies.txt` (FSM с файлом) |

## Полезные команды для диагностики

```bash
# логи бота
docker compose logs -f bot

# метрики скачивания / заливки
docker compose logs bot | grep -E "METRIC|PRIMARY|Fallback"

# здоровье WARP
docker compose exec warp curl -x socks5://127.0.0.1:9091 -s https://www.cloudflare.com/cdn-cgi/trace

# перезапуск только бота после изменений
docker compose up -d --build bot
```
