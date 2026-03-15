"""Отправка больших файлов через Pyrogram (MTProto)
Используется когда файл > 50 МБ — стандартный Bot API не справляется.
Pyrogram + TgCrypto — быстрая загрузка через MTProto, лимит 2 ГБ.
"""
import logging
import os
import time

from pyrogram import Client

from bot.config import settings

logger = logging.getLogger(__name__)

# глобальный клиент Pyrogram
_client: Client | None = None
# ссылка на aiogram Bot (для обновления прогресса)
_aiogram_bot = None


async def init_pyrogram(aiogram_bot=None) -> None:
    """Запускает Pyrogram-клиент как бот"""
    global _client, _aiogram_bot

    _aiogram_bot = aiogram_bot

    if not settings.telethon_enabled:
        logger.info("Pyrogram выключен (нет API_ID/API_HASH)")
        return

    _client = Client(
        "pyrogram_bot",
        api_id=settings.api_id,
        api_hash=settings.api_hash,
        bot_token=settings.bot_token,
        in_memory=True,  # без файла сессии
        no_updates=True,  # не обрабатываем update-ы (это делает aiogram)
    )

    await _client.start()
    me = await _client.get_me()
    logger.info(f"Pyrogram подключён как @{me.username}")


async def stop_pyrogram() -> None:
    """Останавливает Pyrogram"""
    global _client, _aiogram_bot
    if _client and _client.is_connected:
        await _client.stop()
        logger.info("Pyrogram отключён")
    _client = None
    _aiogram_bot = None


def is_available() -> bool:
    """Проверяет, готов ли Pyrogram"""
    return _client is not None and _client.is_connected


def _make_progress_callback(chat_id: int, file_size_mb: float, status_msg=None):
    """Создаёт callback для прогресса загрузки.
    Обновляет сообщение с полоской прогресса.
    """
    last_reported = [0]
    start_time = [time.time()]
    import asyncio

    async def _update_msg(text):
        """Обновляет сообщение через aiogram"""
        if not status_msg or not _aiogram_bot:
            return
        try:
            await _aiogram_bot.edit_message_text(
                text=text,
                chat_id=chat_id,
                message_id=status_msg.message_id,
                parse_mode="HTML",
            )
        except Exception:
            pass

    async def callback(current, total):
        if total == 0:
            return

        percent = int(current / total * 100)

        # обновляем каждые 15%
        if percent - last_reported[0] >= 15 or percent >= 100:
            last_reported[0] = percent

            elapsed = time.time() - start_time[0]
            if elapsed > 0 and current > 0:
                speed_mbs = (current / 1024 / 1024) / elapsed
                remaining_mb = (total - current) / 1024 / 1024
                eta_sec = int(remaining_mb / speed_mbs) if speed_mbs > 0 else 0
                eta_str = (
                    f"{eta_sec // 60}:{eta_sec % 60:02d}"
                    if eta_sec > 60
                    else f"{eta_sec} сек"
                )
            else:
                speed_mbs = 0
                eta_str = "..."

            # полоска прогресса
            filled = int(percent / 10)
            bar = "█" * filled + "░" * (10 - filled)

            logger.info(
                f"Upload: {percent}% "
                f"({current / 1024 / 1024:.0f}/{total / 1024 / 1024:.0f} МБ, "
                f"{speed_mbs:.1f} МБ/с)"
            )

            # обновляем сообщение юзеру
            text = (
                f"📤 <b>Загружаю видео...</b>\n\n"
                f"{bar} {percent}%\n"
                f"📦 {file_size_mb:.0f} МБ • "
                f"⚡ {speed_mbs:.1f} МБ/с • "
                f"⏱ ~{eta_str}"
            )
            await _update_msg(text)

    return callback


async def send_video(
    chat_id: int,
    file_path: str,
    caption: str = "",
    duration: int | None = None,
    status_msg=None,
) -> str | None:
    """Отправляет видео через Pyrogram с прогресс-баром"""
    if not is_available():
        raise RuntimeError("Pyrogram не подключён")

    try:
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        logger.info(
            f"Pyrogram: отправляю видео {file_size_mb:.1f} МБ в чат {chat_id}"
        )

        progress = _make_progress_callback(chat_id, file_size_mb, status_msg)

        await _client.send_video(
            chat_id=chat_id,
            video=file_path,
            caption=caption,
            duration=duration or 0,
            supports_streaming=True,
            progress=progress,
        )

        logger.info(f"Pyrogram: видео отправлено в чат {chat_id}")
        return None

    except Exception as e:
        logger.error(f"Pyrogram: ошибка отправки видео: {e}")
        raise


async def send_audio(
    chat_id: int,
    file_path: str,
    caption: str = "",
    title: str = "",
    duration: int | None = None,
    status_msg=None,
) -> str | None:
    """Отправляет аудио через Pyrogram"""
    if not is_available():
        raise RuntimeError("Pyrogram не подключён")

    try:
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        logger.info(
            f"Pyrogram: отправляю аудио {file_size_mb:.1f} МБ в чат {chat_id}"
        )

        progress = _make_progress_callback(chat_id, file_size_mb, status_msg)

        await _client.send_audio(
            chat_id=chat_id,
            audio=file_path,
            caption=caption,
            title=title,
            performer="YouTube",
            duration=duration or 0,
            progress=progress,
        )

        logger.info(f"Pyrogram: аудио отправлено в чат {chat_id}")
        return None

    except Exception as e:
        logger.error(f"Pyrogram: ошибка отправки аудио: {e}")
        raise
