"""Отправка больших файлов через Telethon (MTProto)
Используется когда файл > 50 МБ — стандартный Bot API не справляется.
Telethon подключается к Telegram напрямую через MTProto, лимит 2 ГБ.
"""
import logging
import os

from telethon import TelegramClient
from telethon.sessions import StringSession

from bot.config import settings

logger = logging.getLogger(__name__)

# глобальный клиент Telethon (инициализируется при старте бота)
_client: TelegramClient | None = None


async def init_telethon() -> None:
    """Запускает Telethon-клиент как бот"""
    global _client

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
    global _client
    if _client and _client.is_connected():
        await _client.disconnect()
        logger.info("Telethon отключён")
    _client = None


def is_available() -> bool:
    """Проверяет, готов ли Telethon к работе"""
    return _client is not None and _client.is_connected()


async def send_video(
    chat_id: int,
    file_path: str,
    caption: str = "",
    duration: int | None = None,
) -> str | None:
    """Отправляет видео через Telethon, возвращает file_id (для кэша)

    Работает с файлами до 2 ГБ.
    Возвращает None если file_id не удалось получить.
    """
    if not is_available():
        raise RuntimeError("Telethon не подключён")

    try:
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        logger.info(
            f"Telethon: отправляю видео {file_size_mb:.1f} МБ в чат {chat_id}"
        )

        # отправляем видео
        result = await _client.send_file(
            entity=chat_id,
            file=file_path,
            caption=caption,
            supports_streaming=True,  # чтобы видео играло сразу
            video_note=False,
            attributes=None,  # Telethon сам определит атрибуты видео
        )

        logger.info(f"Telethon: видео отправлено в чат {chat_id}")

        # пытаемся достать file_id для кэша
        # Telethon возвращает объект Message с document/video
        if result and result.video:
            # конвертируем Telethon file reference в Bot API file_id
            # к сожалению, они несовместимы — кэш по file_id не сработает
            # но файл отправлен, это главное
            return None

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

        result = await _client.send_file(
            entity=chat_id,
            file=file_path,
            caption=caption,
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
