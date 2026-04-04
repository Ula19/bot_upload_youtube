"""Cobalt API клиент — скачивание YouTube без cookies
Cobalt сам решает poToken/n-challenge через yt-session-generator.
"""
import asyncio
import json
import logging
import os
import subprocess
import tempfile

import aiohttp

from bot.config import settings

logger = logging.getLogger(__name__)

# маппинг качества: наш format_key → параметры Cobalt
_QUALITY_MAP = {
    "video_360": {"videoQuality": "360", "youtubeVideoCodec": "h264"},
    "video_480": {"videoQuality": "480", "youtubeVideoCodec": "h264"},
    "video_720": {"videoQuality": "720", "youtubeVideoCodec": "h264"},
    "video_1080": {"videoQuality": "1080", "youtubeVideoCodec": "h264"},
    "video_1440": {"videoQuality": "1440", "youtubeVideoCodec": "h264"},
}

# таймауты: 30 сек на запрос к API, 10 мин на скачивание файла
_API_TIMEOUT = aiohttp.ClientTimeout(total=30)
_DOWNLOAD_TIMEOUT = aiohttp.ClientTimeout(total=600)


class CobaltError(Exception):
    """Ошибка Cobalt API"""
    pass


class CobaltClient:
    """Клиент для Cobalt API v11"""

    def __init__(self):
        self.api_url = settings.cobalt_api_url.rstrip("/")
        self.download_dir = tempfile.mkdtemp(prefix="cobalt_")
        self._available = None  # кэш проверки доступности

    async def is_available(self) -> bool:
        """Проверяет доступен ли Cobalt API"""
        try:
            async with aiohttp.ClientSession(timeout=_API_TIMEOUT) as session:
                async with session.get(self.api_url) as resp:
                    self._available = resp.status == 200
                    return self._available
        except Exception:
            self._available = False
            return False

    async def download_video(self, url: str, quality: str = "720") -> dict:
        """Скачивает видео через Cobalt.
        Возвращает {"file_path": ..., "media_type": "video"}
        """
        format_key = f"video_{quality}"
        params = _QUALITY_MAP.get(format_key, _QUALITY_MAP["video_720"])

        body = {
            "url": url,
            "videoQuality": params["videoQuality"],
            "youtubeVideoCodec": params["youtubeVideoCodec"],
        }

        tunnel_url = await self._request(body)
        file_path = await self._download_file(tunnel_url, f"video_{quality}.mp4")

        return {
            "file_path": file_path,
            "media_type": "video",
            "format_key": format_key,
        }

    async def download_audio(self, url: str) -> dict:
        """Скачивает аудио (MP3) через Cobalt.
        Возвращает {"file_path": ..., "media_type": "audio"}
        """
        body = {
            "url": url,
            "downloadMode": "audio",
            "audioFormat": "mp3",
        }

        tunnel_url = await self._request(body)
        file_path = await self._download_file(tunnel_url, "audio.mp3")

        return {
            "file_path": file_path,
            "media_type": "audio",
            "format_key": "audio",
        }

    async def _request(self, body: dict) -> str:
        """Отправляет запрос к Cobalt API, возвращает URL для скачивания"""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession(timeout=_API_TIMEOUT) as session:
            async with session.post(self.api_url, json=body, headers=headers) as resp:
                data = await resp.json()
                logger.info("Cobalt ответ: status=%s, data=%s", resp.status, data)

                if resp.status != 200:
                    error_msg = data.get("error", {}).get("code", "unknown_error")
                    raise CobaltError(f"Cobalt API ошибка: {error_msg}")

                status = data.get("status")
                if status in ("tunnel", "redirect"):
                    logger.info("Cobalt URL: %s", data["url"])
                    return data["url"]

                # picker — несколько вариантов (плейлист), берём первый
                if status == "picker":
                    items = data.get("picker", [])
                    if items:
                        return items[0]["url"]

                raise CobaltError(f"Неожиданный ответ Cobalt: {status}")

    async def _download_file(self, url: str, filename: str) -> str:
        """Скачивает файл по tunnel URL"""
        file_path = os.path.join(self.download_dir, filename)

        async with aiohttp.ClientSession(timeout=_DOWNLOAD_TIMEOUT) as session:
            async with session.get(url) as resp:
                logger.info("Tunnel ответ: status=%s, content-type=%s, content-length=%s",
                            resp.status, resp.content_type, resp.headers.get("content-length", "?"))

                if resp.status != 200:
                    body = await resp.text()
                    raise CobaltError(f"Не удалось скачать файл: HTTP {resp.status}, body={body[:200]}")

                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(1024 * 1024):
                        f.write(chunk)

        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        if file_size == 0:
            raise CobaltError("Скачанный файл пуст (0 байт)")

        logger.info("Cobalt: скачан %s (%.1f МБ)",
                     filename, os.path.getsize(file_path) / 1024 / 1024)
        return file_path

    def get_media_info(self, file_path: str) -> dict:
        """Получает width, height, duration из файла через ffprobe"""
        try:
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-print_format", "json",
                    "-show_format", "-show_streams",
                    file_path,
                ],
                capture_output=True, text=True, timeout=10,
            )
            data = json.loads(result.stdout)

            # ищем видео-поток
            for stream in data.get("streams", []):
                if stream.get("codec_type") == "video":
                    return {
                        "width": int(stream.get("width", 0)),
                        "height": int(stream.get("height", 0)),
                        "duration": int(float(data.get("format", {}).get("duration", 0))),
                    }

            # аудио — только duration
            duration = float(data.get("format", {}).get("duration", 0))
            return {"width": 0, "height": 0, "duration": int(duration)}

        except Exception as e:
            logger.warning("ffprobe не смог прочитать файл: %s", e)
            return {"width": 0, "height": 0, "duration": 0}

    def cleanup(self, file_path: str) -> None:
        """Удаляет временный файл"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except OSError as e:
            logger.warning("Не удалось удалить файл Cobalt: %s", e)


# глобальный экземпляр
cobalt_client = CobaltClient()
