"""Отправка больших файлов через Telethon (MTProto)
Используется когда файл > 50 МБ — стандартный Bot API не справляется.
Telethon подключается к Telegram напрямую через MTProto, лимит 2 ГБ.
"""
import asyncio
import logging
import os
import time

from telethon import TelegramClient
from telethon.sessions import StringSession

from bot.config import settings

logger = logging.getLogger(__name__)

# глобальный клиент Telethon (инициализируется при старте бота)
_client: TelegramClient | None = None
# ссылка на aiogram Bot (для отправки прогресса)
_aiogram_bot = None


async def init_telethon(aiogram_bot=None) -> None:
    """Запускает Telethon-клиент как бот"""
    global _client, _aiogram_bot

    _aiogram_bot = aiogram_bot

    if not settings.telethon_enabled:
        logger.info("Telethon выключен (нет API_ID/API_HASH)")
        return

    _client = TelegramClient(
        StringSession(),  # без файла сессии — бот не хранит состояние
        api_id=settings.api_id,
        api_hash=settings.api_hash,
    )

    # подключаемся как бот (через bot_token)
    await _client.start(bot_token=settings.bot_token)
    me = await _client.get_me()
    logger.info(f"Telethon подключён как @{me.username}")


async def stop_telethon() -> None:
    """Останавливает Telethon-клиента"""
    global _client, _aiogram_bot
    if _client and _client.is_connected():
        await _client.disconnect()
        logger.info("Telethon отключён")
    _client = None
    _aiogram_bot = None


def is_available() -> bool:
    """Проверяет, готов ли Telethon к работе"""
    return _client is not None and _client.is_connected()


async def _update_progress_message(chat_id: int, status_msg, progress_data: dict):
    """Обновляет сообщение с прогрессом через aiogram.
    Вызывается периодически из фоновой задачи.
    """
    if not status_msg or not _aiogram_bot:
        return

    percent = progress_data.get("percent", 0)
    file_size_mb = progress_data.get("file_size_mb", 0)
    speed_mbs = progress_data.get("speed_mbs", 0)
    eta_str = progress_data.get("eta_str", "...")

    # полоска прогресса
    filled = int(percent / 10)
    bar = "█" * filled + "░" * (10 - filled)

    text = (
        f"📤 <b>Загружаю видео...</b>\n\n"
        f"{bar} {percent}%\n"
        f"📦 {file_size_mb:.0f} МБ • "
        f"⚡ {speed_mbs:.1f} МБ/с • "
        f"⏱ ~{eta_str}"
    )

    try:
        await _aiogram_bot.edit_message_text(
            text=text,
            chat_id=chat_id,
            message_id=status_msg.message_id,
            parse_mode="HTML",
        )
    except Exception:
        pass  # не критично если не удалось обновить


def _make_progress_callback(chat_id: int, file_size_mb: float, status_msg=None):
    """Создаёт СИНХРОННЫЙ callback для Telethon + планирует обновление сообщения.
    Telethon не вызывает async callbacks корректно — используем sync.
    """
    last_reported = [0]
    start_time = [time.time()]
    loop = asyncio.get_event_loop()

    def callback(current, total):
        if total == 0:
            return

        percent = int(current / total * 100)

        # логи каждые 20%
        if percent - last_reported[0] >= 20 or percent == 100:
            last_reported[0] = percent

            elapsed = time.time() - start_time[0]
            if elapsed > 0 and current > 0:
                speed_mbs = (current / 1024 / 1024) / elapsed
                remaining_mb = (total - current) / 1024 / 1024
                eta_sec = int(remaining_mb / speed_mbs) if speed_mbs > 0 else 0
                eta_str = f"{eta_sec // 60}:{eta_sec % 60:02d}" if eta_sec > 60 else f"{eta_sec} сек"
            else:
                speed_mbs = 0
                eta_str = "..."

            logger.info(
                f"Upload: {percent}% "
                f"({current / 1024 / 1024:.0f}/{total / 1024 / 1024:.0f} МБ, "
                f"{speed_mbs:.1f} МБ/с)"
            )

            # обновляем сообщение через asyncio (не блокируя)
            if status_msg and _aiogram_bot:
                progress_data = {
                    "percent": percent,
                    "file_size_mb": file_size_mb,
                    "speed_mbs": speed_mbs,
                    "eta_str": eta_str,
                }
                try:
                    asyncio.ensure_future(
                        _update_progress_message(chat_id, status_msg, progress_data)
                    )
                except Exception:
                    pass

    return callback


async def send_video(
    chat_id: int,
    file_path: str,
    caption: str = "",
    duration: int | None = None,
    status_msg=None,
) -> str | None:
    """Отправляет видео через Telethon с прогресс-баром.
    status_msg — сообщение aiogram для отображения прогресса.
    """
    if not is_available():
        raise RuntimeError("Telethon не подключён")

    try:
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        logger.info(
            f"Telethon: отправляю видео {file_size_mb:.1f} МБ в чат {chat_id}"
        )

        progress = _make_progress_callback(chat_id, file_size_mb, status_msg)

        result = await _client.send_file(
            entity=chat_id,
            file=file_path,
            caption=caption,
            supports_streaming=True,
            progress_callback=progress,
        )

        logger.info(f"Telethon: видео отправлено в чат {chat_id}")
        return None

    except Exception as e:
        logger.error(f"Telethon: ошибка отправки видео: {e}")
        raise


async def send_audio(
    chat_id: int,
    file_path: str,
    caption: str = "",
    title: str = "",
    duration: int | None = None,
    status_msg=None,
) -> str | None:
    """Отправляет аудио через Telethon"""
    if not is_available():
        raise RuntimeError("Telethon не подключён")

    try:
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        logger.info(
            f"Telethon: отправляю аудио {file_size_mb:.1f} МБ в чат {chat_id}"
        )

        from telethon.tl.types import DocumentAttributeAudio

        progress = _make_progress_callback(chat_id, file_size_mb, status_msg)

        result = await _client.send_file(
            entity=chat_id,
            file=file_path,
            caption=caption,
            progress_callback=progress,
            attributes=[
                DocumentAttributeAudio(
                    duration=duration or 0,
                    title=title,
                    performer="YouTube",
                ),
            ],
        )

        logger.info(f"Telethon: аудио отправлено в чат {chat_id}")
        return None

    except Exception as e:
        logger.error(f"Telethon: ошибка отправки аудио: {e}")
        raise
