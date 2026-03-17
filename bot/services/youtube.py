"""Сервис скачивания YouTube — через Cobalt API
Поддерживает: видео (MP4), аудио (MP3), Shorts
Cobalt работает как self-hosted Docker-сервис
"""
import asyncio
import logging
import os
import tempfile
from dataclasses import dataclass

import aiohttp

from bot.config import settings

logger = logging.getLogger(__name__)

# лимит файла (Local Bot API — 2 ГБ)
MAX_FILE_SIZE = settings.max_file_size


@dataclass
class VideoInfo:
    """Информация о видео (до скачивания)"""
    title: str
    duration: int  # в секундах
    thumbnail: str | None = None
    uploader: str | None = None


@dataclass
class DownloadResult:
    """Результат скачивания"""
    file_path: str
    media_type: str       # video или audio
    title: str
    duration: int | None = None
    format_key: str = ""  # video_360, video_720, audio


class YouTubeDownloader:
    """Скачивает контент с YouTube через Cobalt API"""

    def __init__(self):
        self.download_dir = tempfile.mkdtemp(prefix="yt_bot_")
        self.cobalt_url = settings.cobalt_url
        logger.info("Cobalt API: %s", self.cobalt_url)

    async def get_info(self, url: str) -> VideoInfo:
        """Получает метаданные видео через YouTube oEmbed API"""
        oembed_url = (
            f"https://www.youtube.com/oembed"
            f"?url={url}&format=json"
        )

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(oembed_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return VideoInfo(
                            title=data.get("title", "Без названия"),
                            duration=0,  # oEmbed не даёт duration
                            thumbnail=data.get("thumbnail_url"),
                            uploader=data.get("author_name"),
                        )
        except Exception as e:
            logger.warning("oEmbed не сработал: %s", e)

        # если oEmbed не сработал — возвращаем заглушку
        return VideoInfo(title="YouTube видео", duration=0)

    async def download_video(
        self, url: str, quality: str = "720"
    ) -> DownloadResult:
        """Скачивает видео через Cobalt API"""
        # запрос к Cobalt
        cobalt_data = {
            "url": url,
            "videoQuality": quality,
            "youtubeVideoCodec": "h264",
        }

        file_url = await self._request_cobalt(cobalt_data)
        file_path = os.path.join(
            self.download_dir, f"video_{quality}p.mp4"
        )

        await self._download_file(file_url, file_path)

        # проверяем размер
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            self._remove_file(file_path)
            raise FileTooLargeError(
                f"Видео слишком большое "
                f"({file_size / 1024 / 1024:.0f} МБ)"
            )

        return DownloadResult(
            file_path=file_path,
            media_type="video",
            title="YouTube Video",
            format_key=f"video_{quality}",
        )

    async def download_audio(self, url: str) -> DownloadResult:
        """Скачивает аудио (MP3) через Cobalt API"""
        cobalt_data = {
            "url": url,
            "downloadMode": "audio",
            "audioFormat": "mp3",
            "audioBitrate": "128",
        }

        file_url = await self._request_cobalt(cobalt_data)
        file_path = os.path.join(
            self.download_dir, "audio.mp3"
        )

        await self._download_file(file_url, file_path)

        # проверяем размер
        file_size = os.path.getsize(file_path)
        if file_size > MAX_FILE_SIZE:
            self._remove_file(file_path)
            raise FileTooLargeError(
                f"Аудио слишком большое ({file_size / 1024 / 1024:.0f} МБ)"
            )

        return DownloadResult(
            file_path=file_path,
            media_type="audio",
            title="YouTube Audio",
            format_key="audio",
        )

    async def _request_cobalt(self, data: dict) -> str:
        """Отправляет запрос к Cobalt API и возвращает URL файла"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.cobalt_url,
                json=data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=30),
            ) as resp:
                result = await resp.json()
                logger.info("Cobalt ответ: status=%s", result.get("status"))

                status = result.get("status")

                if status in ("tunnel", "redirect"):
                    return result["url"]

                if status == "picker":
                    # несколько вариантов — берём первый
                    items = result.get("picker", [])
                    if items:
                        return items[0].get("url", "")

                if status == "error":
                    error_code = result.get("error", {}).get("code", "unknown")
                    raise RuntimeError(
                        f"Cobalt ошибка: {error_code}"
                    )

                raise RuntimeError(
                    f"Cobalt: неожиданный ответ ({status})"
                )

    async def _download_file(self, url: str, file_path: str) -> None:
        """Скачивает файл по URL во временную папку"""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:
                if resp.status != 200:
                    raise RuntimeError(
                        f"Ошибка скачивания: HTTP {resp.status}"
                    )

                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(8192):
                        f.write(chunk)

        logger.info("Скачан: %s (%.1f МБ)",
                     file_path, os.path.getsize(file_path) / 1024 / 1024)

    def cleanup(self, result: DownloadResult) -> None:
        """Удаляет временные файлы после отправки"""
        self._remove_file(result.file_path)

    def _remove_file(self, path: str) -> None:
        """Безопасно удаляет файл"""
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info("Удалён: %s", path)
        except OSError as e:
            logger.warning("Не удалось удалить файл: %s", e)


class FileTooLargeError(Exception):
    """Файл превышает лимит Telegram"""
    pass


# глобальный экземпляр
downloader = YouTubeDownloader()
