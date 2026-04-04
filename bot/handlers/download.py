"""Хэндлер скачивания — обрабатывает ссылки YouTube
Флоу: ссылка → выбор формата → выбор качества → скачивание → отправка
"""
import asyncio
import logging
import os
import time

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, FSInputFile, Message

from bot.database import async_session
from bot.database.crud import (
    get_cached_download,
    get_or_create_user,
    get_user_language,
    save_download,
)
from bot.i18n import t
from bot.keyboards.inline import (
    get_audio_suggest_keyboard,
    get_back_keyboard,
    get_format_keyboard,
    get_quality_keyboard,
)
from bot.services.youtube import FileTooLargeError, downloader
from bot.utils.helpers import clean_youtube_url, is_youtube_url
from bot.config import settings
from bot.emojis import E

logger = logging.getLogger(__name__)
router = Router()

# минимальный интервал обновления прогресса (Telegram лимит ~30 ред/мин)
PROGRESS_UPDATE_INTERVAL = 4

# чтобы не спамить админа — уведомляем только один раз
_admin_notified = False


def _make_progress_bar(percent: int, dl_mb: float, total_mb: float) -> str:
    """Рисует полоску прогресса"""
    filled = int(percent / 100 * 15)
    bar = "█" * filled + "░" * (15 - filled)
    return (
        f"{E['clock']} Скачиваю... {percent}%\n"
        f"{bar}\n"
        f"{dl_mb:.0f} МБ / {total_mb:.0f} МБ"
    )


# FSM для сохранения URL между шагами выбора
class DownloadStates(StatesGroup):
    waiting_format = State()
    waiting_quality = State()


@router.message(F.text)
async def handle_youtube_link(message: Message, state: FSMContext) -> None:
    """Обработка текстовых сообщений — ищем ссылки YouTube"""
    text = message.text.strip()

    async with async_session() as session:
        lang = await get_user_language(session, message.from_user.id)

    # проверяем что это ссылка на YouTube
    if not is_youtube_url(text):
        await message.answer(
            t("download.not_youtube", lang),
            parse_mode="HTML",
        )
        return

    clean_url = clean_youtube_url(text)

    # получаем инфо о видео
    try:
        status_msg = await message.answer(t("download.fetching_info", lang))
        info = await downloader.get_info(clean_url)

        # сохраняем URL и инфо в FSM
        await state.set_state(DownloadStates.waiting_format)
        await state.update_data(
            url=clean_url,
            title=info.title,
            duration=info.duration,
            qualities=info.qualities,
            msg_id=message.message_id,
        )

        # форматируем длительность
        duration_str = _format_duration(info.duration)

        await status_msg.edit_text(
            t("download.info", lang,
              title=info.title,
              duration=duration_str,
              uploader=info.uploader or "—"),
            reply_markup=get_format_keyboard(lang),
            parse_mode="HTML",
        )

    except Exception as e:
        logger.error(f"Ошибка получения инфо: {e}")
        error_text = _get_error_text(str(e), lang)
        if status_msg:
            await status_msg.edit_text(error_text)
        else:
            await message.answer(error_text)


@router.callback_query(F.data == "fmt_video")
async def choose_video_format(callback: CallbackQuery, state: FSMContext) -> None:
    """Юзер выбрал видео — показываем качество с размерами"""
    async with async_session() as session:
        lang = await get_user_language(session, callback.from_user.id)

    data = await state.get_data()
    qualities = data.get("qualities")
    await state.set_state(DownloadStates.waiting_quality)

    await callback.message.edit_text(
        t("download.choose_quality", lang),
        reply_markup=get_quality_keyboard(lang, qualities),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data == "fmt_audio")
async def download_audio(callback: CallbackQuery, state: FSMContext) -> None:
    """Юзер выбрал аудио — скачиваем MP3"""
    data = await state.get_data()
    url = data.get("url")
    await state.clear()

    # отвечаем на callback СРАЗУ (Telegram даёт 30 сек)
    await callback.answer()

    if not url:
        await callback.message.answer(f"{E['cross']} Ссылка не найдена, отправь заново")
        return

    async with async_session() as session:
        lang = await get_user_language(session, callback.from_user.id)

    await _process_download(
        callback.message, url, "audio", callback.from_user, lang, state
    )


@router.callback_query(F.data.startswith("quality_"))
async def choose_quality(callback: CallbackQuery, state: FSMContext) -> None:
    """Юзер выбрал качество — скачиваем видео"""
    quality = callback.data.replace("quality_", "")  # "360" или "720"
    data = await state.get_data()
    url = data.get("url")
    await state.clear()

    # отвечаем на callback СРАЗУ (Telegram даёт 30 сек)
    await callback.answer()

    if not url:
        await callback.message.answer(f"{E['cross']} Ссылка не найдена, отправь заново")
        return

    async with async_session() as session:
        lang = await get_user_language(session, callback.from_user.id)

    format_key = f"video_{quality}"
    await _process_download(
        callback.message, url, format_key, callback.from_user, lang, state
    )


async def _process_download(
    message: Message,
    url: str,
    format_key: str,
    user,
    lang: str = "ru",
    state: FSMContext | None = None,
) -> None:
    """Скачивает и отправляет медиа"""
    # проверяем кэш
    async with async_session() as session:
        await get_or_create_user(
            session=session,
            telegram_id=user.id,
            username=user.username,
            full_name=user.full_name,
        )
        cached = await get_cached_download(session, url, format_key)

    if cached:
        logger.info(f"Кэш найден для {url} [{format_key}]")
        await _send_cached(message, cached.file_id, cached.media_type)
        return

    # скачиваем
    status_msg = await message.edit_text(t("download.processing", lang))

    # callback для обновления прогресса
    last_progress_update = {"time": 0}
    # захватываем loop ДО executor (внутри потока get_event_loop() не работает)
    loop = asyncio.get_event_loop()

    def on_progress(dl_mb: float, total_mb: float, percent: int):
        """yt-dlp вызывает это из другого потока, шедулим обновление в asyncio"""
        now = time.time()
        if now - last_progress_update["time"] < PROGRESS_UPDATE_INTERVAL:
            return
        last_progress_update["time"] = now

        text = _make_progress_bar(percent, dl_mb, total_mb)
        # шедулим в event loop (хук вызывается из другого потока)
        try:
            asyncio.run_coroutine_threadsafe(
                _safe_edit(status_msg, text), loop
            )
        except Exception:
            pass

    result = None
    try:
        if format_key == "audio":
            result = await downloader.download_audio(url, on_progress)
        else:
            quality = format_key.replace("video_", "")
            result = await downloader.download_video(url, quality, on_progress)

        file_id = await _send_media(message, result, status_msg, lang)

        # если сработал fallback — уведомляем админа (один раз)
        if downloader.auth_failed:
            await _notify_admin_auth_failed(message.bot)

        # сохраняем в кэш
        if file_id:
            actual_format_key = result.format_key or format_key
            async with async_session() as session:
                await save_download(
                    session=session,
                    youtube_url=url,
                    format_key=actual_format_key,
                    file_id=file_id,
                    media_type=result.media_type,
                )
                user_obj = await get_or_create_user(
                    session=session,
                    telegram_id=user.id,
                    username=user.username,
                    full_name=user.full_name,
                )
                user_obj.download_count += 1
                await session.commit()

        # удаляем статусное сообщение
        try:
            await status_msg.delete()
        except Exception:
            pass

    except FileTooLargeError:
        # видео слишком большое даже в 360p — предлагаем аудио
        await status_msg.edit_text(
            t("error.too_large_suggest_audio", lang),
            reply_markup=get_audio_suggest_keyboard(lang),
            parse_mode="HTML",
        )
        # восстанавливаем FSM с URL чтобы кнопка "Скачать аудио" работала
        if state:
            await state.set_state(DownloadStates.waiting_format)
            await state.update_data(url=url)

    except Exception as e:
        logger.error(f"Ошибка скачивания {url}: {e}")
        error_text = _get_error_text(str(e), lang)
        try:
            await status_msg.edit_text(error_text)
        except Exception:
            await message.answer(error_text)

    finally:
        if result:
            downloader.cleanup(result)


async def _send_media(message: Message, result, status_msg=None, lang="ru") -> str | None:
    """Отправляет медиа юзеру и возвращает file_id.
    Через Local Bot API — файлы до 2 ГБ без ограничений.
    """
    file = FSInputFile(result.file_path)

    # Уведомляем пользователя перед долгой отправкой
    if status_msg:
        try:
            await status_msg.edit_text(t("download.uploading", lang))
        except Exception:
            pass

    if result.media_type == "video":
        promo = t("download.promo", lang, bot_username=settings.bot_username)
        sent = await message.answer_video(
            video=file,
            caption=f"{E['video']} {result.title}{promo}",
            duration=int(result.duration) if result.duration else None,
            width=result.width,
            height=result.height,
        )
        return sent.video.file_id

    elif result.media_type == "audio":
        promo = t("download.promo", lang, bot_username=settings.bot_username)
        sent = await message.answer_audio(
            audio=file,
            caption=f"{E['audio']} {result.title}{promo}",
            duration=int(result.duration) if result.duration else None,
            title=result.title,
        )
        return sent.audio.file_id

    return None


async def _send_cached(
    message: Message, file_id: str, media_type: str
) -> None:
    """Отправляет из кэша по file_id"""
    try:
        if media_type == "video":
            await message.answer_video(video=file_id, caption=f"{E['video']} YouTube Video")
        elif media_type == "audio":
            await message.answer_audio(audio=file_id, caption=f"{E['audio']} YouTube Audio")
    except Exception as e:
        logger.error(f"Ошибка отправки из кэша: {e}")
        await message.answer(f"{E['warning']} Кэш устарел. Отправь ссылку ещё раз.")


async def _safe_edit(msg: Message, text: str) -> None:
    """Безопасно обновляет сообщение (игнорирует ошибки лимита Telegram)"""
    try:
        await msg.edit_text(text)
    except Exception:
        pass


def _format_duration(seconds: int) -> str:
    """Форматирует секунды в MM:SS или HH:MM:SS"""
    if not seconds:
        return "—"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def _get_error_text(error: str, lang: str = "ru") -> str:
    """Человеко-понятное сообщение об ошибке"""
    error_lower = error.lower()

    if "private" in error_lower or "login" in error_lower:
        return t("error.private", lang)
    elif "not found" in error_lower or "404" in error_lower:
        return t("error.not_found", lang)
    elif "unavailable" in error_lower:
        return t("error.unavailable", lang)
    elif "too large" in error_lower or "50 мб" in error_lower:
        return t("error.too_large", lang)
    elif "timeout" in error_lower:
        return t("error.timeout", lang)
    elif "available in your country" in error_lower:
        return t("error.geo_blocked", lang)
    elif "age" in error_lower:
        return t("error.age_restricted", lang)
    else:
        return t("error.generic", lang)


async def _notify_admin_auth_failed(bot) -> None:
    """Уведомляет админа что cookies протухли (один раз)"""
    global _admin_notified
    if _admin_notified:
        return
    _admin_notified = True

    text = (
        f"{E['warning']} <b>Cookies протухли!</b>\n\n"
        "Бот переключился на ios/android.\n"
        "Качество видео снижено (360-480p).\n\n"
        "Для восстановления 720p:\n"
        "1. Откройте Firefox в приватном режиме\n"
        "2. Войдите в YouTube\n"
        '3. Экспортируйте cookies расширением "Get cookies.txt LOCALLY"\n'
        "4. Отправьте файл боту командой /update_cookies"
    )

    for admin_id in settings.admin_id_list:
        try:
            await bot.send_message(admin_id, text, parse_mode="HTML")
            logger.info("Админ %s уведомлён о протухших cookies", admin_id)
        except Exception as e:
            logger.warning("Не удалось уведомить админа %s: %s", admin_id, e)

