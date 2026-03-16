# 🚀 Деплой YouTube-бота на сервер

## Требования

- Ubuntu 22.04+
- Docker + Docker Compose
- Git

## 1. Установка Docker (если нет)

```bash
# обновляем пакеты
sudo apt update && sudo apt upgrade -y

# ставим Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# перезайти в SSH чтобы группа подхватилась
exit
```

## 2. Клонирование проекта

```bash
cd ~
git clone https://github.com/YOUR_USERNAME/bot_4_youtube.git
cd bot_4_youtube
```

## 3. Настройка переменных окружения

```bash
cp .env.example .env
nano .env
```

Заполни все переменные:

```env
BOT_TOKEN=токен_от_BotFather
DB_HOST=postgres
DB_PORT=5432
DB_NAME=bot_4_youtube
DB_USER=bot_4_youtube
DB_PASSWORD=СИЛЬНЫЙ_ПАРОЛЬ
ADMIN_IDS=твой_telegram_id
ADMIN_USERNAME=твой_username
API_ID=api_id_с_my.telegram.org
API_HASH=api_hash_с_my.telegram.org
BOT_API_URL=http://bot-api:8081
```

> **Важно**: `API_ID` и `API_HASH` получить на https://my.telegram.org

## 4. Запуск

```bash
docker compose up -d --build
```

Проверка что всё работает:

```bash
docker compose ps          # статус контейнеров
docker compose logs bot    # логи бота
```

## 5. Порты

| Сервис     | Порт  | Описание                   |
|------------|-------|----------------------------|
| bot-api    | 8081  | Local Bot API (файлы >50МБ)|
| postgres   | —     | Без внешнего порта         |
| bot        | —     | Без порта (polling)        |

> PostgreSQL и бот не выставлены наружу — это безопасно.

## 6. Обновление на сервере

```bash
cd ~/bot_4_youtube
git pull
docker compose up -d --build bot
```

Если изменился `docker-compose.yml`:

```bash
docker compose up -d --build
```

## 7. Бэкап базы данных

```bash
# создать бэкап
docker compose exec postgres pg_dump -U bot_4_youtube bot_4_youtube > backup.sql

# восстановить
cat backup.sql | docker compose exec -T postgres psql -U bot_4_youtube bot_4_youtube
```

## 8. Полезные команды

```bash
docker compose logs -f bot       # логи в реалтайме
docker compose restart bot       # перезапуск бота
docker compose down              # остановить всё
docker compose down -v           # остановить + удалить данные (ОСТОРОЖНО!)
```
