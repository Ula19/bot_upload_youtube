"""Отправка больших файлов через Pyrogram (MTProto)
Используется когда файл > 50 МБ — стандартный Bot API не справляется.
Pyrogram + TgCrypto — быстрая загрузка через MTProto, лимит 2 ГБ.

Пул из нескольких клиентов — параллельные загрузки не блокируют друг друга.
"""
import asyncio
import logging
import os
import time

from pyrogram import Client

from bot.config import settings

logger = logging.getLogger(__name__)

# пул Pyrogram-клиентов для параллельных загрузок
POOL_SIZE = 3
_pool: list[Client] = []
_pool_semaphore: asyncio.Semaphore | None = None
_pool_locks: list[asyncio.Lock] = []

# ссылка на aiogram Bot (для обновления прогресса)
_aiogram_bot = None


async def init_pyrogram(aiogram_bot=None) -> None:
    """Запускает пул Pyrogram-клиентов"""
    global _pool, _pool_semaphore, _pool_locks, _aiogram_bot

    _aiogram_bot = aiogram_bot

    if not settings.telethon_enabled:
        logger.info("Pyrogram выключен (нет API_ID/API_HASH)")
        return

    _pool_semaphore = asyncio.Semaphore(POOL_SIZE)
    _pool_locks = [asyncio.Lock() for _ in range(POOL_SIZE)]

    # создаём несколько клиентов — каждый со своим MTProto-соединением
    for i in range(POOL_SIZE):
        client = Client(
            f"pyrogram_worker_{i}",
            api_id=settings.api_id,
            api_hash=settings.api_hash,
            bot_token=settings.bot_token,
            in_memory=True,
            no_updates=True,
        )
        await client.start()
        _pool.append(client)

    me = await _pool[0].get_me()
    logger.info(
        f"Pyrogram пул ({POOL_SIZE} воркеров) подключён как @{me.username}"
    )


async def stop_pyrogram() -> None:
    """Останавливает все Pyrogram-клиенты"""
    global _pool, _aiogram_bot
    for client in _pool:
        if client.is_connected:
            await client.stop()
    _pool.clear()
    _aiogram_bot = None
    logger.info("Pyrogram пул остановлен")


def is_available() -> bool:
    """Проверяет, есть ли рабочие клиенты"""
    return len(_pool) > 0 and any(c.is_connected for c in _pool)


async def _acquire_client() -> tuple[Client, int]:
    """Берёт свободный клиент из пула.
    Если все заняты — ждёт освобождения.
    """
    await _pool_semaphore.acquire()

    # ищем незалоченный клиент
    for i, lock in enumerate(_pool_locks):
        if not lock.locked():
            await lock.acquire()
            return _pool[i], i

    # fallback — берём первый доступный (ждём)
    for i, lock in enumerate(_pool_locks):
        await lock.acquire()
        return _pool[i], i

    raise RuntimeError("Нет свободных Pyrogram воркеров")


def _release_client(index: int) -> None:
    """Возвращает клиент в пул"""
    _pool_locks[index].release()
    _pool_semaphore.release()


def _make_progress_callback(chat_id: int, file_size_mb: float, status_msg=None):
    """Создаёт callback для прогресса загрузки"""
    last_reported = [0]
    start_time = [time.time()]

    async def _update_msg(text):
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

            filled = int(percent / 10)
            bar = "█" * filled + "░" * (10 - filled)

            logger.info(
                f"Upload: {percent}% "
                f"({current / 1024 / 1024:.0f}/{total / 1024 / 1024:.0f} МБ, "
                f"{speed_mbs:.1f} МБ/с)"
            )

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
    """Отправляет видео через свободный Pyrogram-клиент из пула"""
    if not is_available():
        raise RuntimeError("Pyrogram не подключён")

    client, idx = await _acquire_client()
    try:
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        logger.info(
            f"Pyrogram[{idx}]: отправляю видео "
            f"{file_size_mb:.1f} МБ в чат {chat_id}"
        )

        progress = _make_progress_callback(chat_id, file_size_mb, status_msg)

        await client.send_video(
            chat_id=chat_id,
            video=file_path,
            caption=caption,
            duration=duration or 0,
            supports_streaming=True,
            progress=progress,
        )

        logger.info(f"Pyrogram[{idx}]: видео отправлено в чат {chat_id}")
        return None

    except Exception as e:
        logger.error(f"Pyrogram[{idx}]: ошибка отправки видео: {e}")
        raise
    finally:
        _release_client(idx)


async def send_audio(
    chat_id: int,
    file_path: str,
    caption: str = "",
    title: str = "",
    duration: int | None = None,
    status_msg=None,
) -> str | None:
    """Отправляет аудио через свободный Pyrogram-клиент из пула"""
    if not is_available():
        raise RuntimeError("Pyrogram не подключён")

    client, idx = await _acquire_client()
    try:
        file_size_mb = os.path.getsize(file_path) / 1024 / 1024
        logger.info(
            f"Pyrogram[{idx}]: отправляю аудио "
            f"{file_size_mb:.1f} МБ в чат {chat_id}"
        )

        progress = _make_progress_callback(chat_id, file_size_mb, status_msg)

        await client.send_audio(
            chat_id=chat_id,
            audio=file_path,
            caption=caption,
            title=title,
            performer="YouTube",
            duration=duration or 0,
            progress=progress,
        )

        logger.info(f"Pyrogram[{idx}]: аудио отправлено в чат {chat_id}")
        return None

    except Exception as e:
        logger.error(f"Pyrogram[{idx}]: ошибка отправки аудио: {e}")
        raise
    finally:
        _release_client(idx)
