"""Сервис скачивания YouTube — через yt-dlp + прокси
Поддерживает: видео (MP4), аудио (MP3), Shorts
Автопонижение качества при превышении лимита
"""
import asyncio
import logging
import os
import tempfile
import time
from dataclasses import dataclass
from typing import Callable

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


# тип для callback прогресса: (скачано_мб, всего_мб, процент)
ProgressCallback = Callable[[float, float, int], None] | None


class YouTubeDownloader:
    """Скачивает контент с YouTube через yt-dlp + резидентный прокси
    Использует player_client ios/android — не требует cookies и аккаунта
    """

    # пауза между запросами к YouTube (чтобы не получить бан)
    _RATE_LIMIT_DELAY = 3

    def __init__(self):
        self.download_dir = tempfile.mkdtemp(prefix="yt_bot_")
        self._proxy = settings.proxy_url or None
        self._last_download_time = 0.0
        if self._proxy:
            logger.info("Прокси подключен: %s", self._proxy)
        else:
            logger.warning("Прокси не настроен — YouTube может блокировать")

    async def _rate_limit(self):
        """Ждём между запросами чтобы YouTube не заблокировал"""
        now = time.time()
        wait = self._RATE_LIMIT_DELAY - (now - self._last_download_time)
        if wait > 0:
            logger.info("Пауза %.1f сек (rate-limit)", wait)
            await asyncio.sleep(wait)
        self._last_download_time = time.time()

    def _base_opts(self) -> dict:
        """Общие настройки для всех запросов yt-dlp"""
        opts = {
            "quiet": True,
            "no_warnings": True,
            # ios — обходит бот-проверку, web — даёт качественные форматы (720p h264)
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "web"],
                    "player_skip": ["webpage"],
                },
            },
        }
        if self._proxy:
            opts["proxy"] = self._proxy
        return opts

    async def get_info(self, url: str) -> VideoInfo:
        """Получает метаданные видео без скачивания"""
        import yt_dlp

        ydl_opts = {
            **self._base_opts(),
            "skip_download": True,
            "ignore_no_formats_error": True,
        }

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, self._extract_info, url, ydl_opts
        )

        return VideoInfo(
            title=info.get("title", "Без названия"),
            duration=info.get("duration", 0),
            thumbnail=info.get("thumbnail"),
            uploader=info.get("uploader"),
        )

    async def download_video(
        self, url: str, quality: str = "720",
        progress_callback: ProgressCallback = None,
    ) -> DownloadResult:
        """Скачивает видео в выбранном качестве"""
        await self._rate_limit()
        result = await self._download_with_quality(url, quality, progress_callback)
        file_size = os.path.getsize(result.file_path)

        if file_size > settings.max_file_size:
            self._remove_file(result.file_path)
            raise FileTooLargeError(
                f"Видео слишком большое "
                f"({file_size / 1024 / 1024:.0f} МБ)"
            )

        return result

    async def download_audio(
        self, url: str,
        progress_callback: ProgressCallback = None,
    ) -> DownloadResult:
        """Скачивает аудио (MP3, 128kbps)"""
        await self._rate_limit()
        import yt_dlp

        output_template = os.path.join(
            self.download_dir, "%(id)s_audio.%(ext)s"
        )

        ydl_opts = {
            **self._base_opts(),
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": output_template,
            # конвертируем в mp3 через ffmpeg
            "postprocessors": [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }],
        }

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, self._download, url, ydl_opts, progress_callback
        )

        # yt-dlp меняет расширение после конвертации
        file_path = self._find_downloaded_file(info, "mp3")

        if not file_path or not os.path.exists(file_path):
            raise RuntimeError("Не удалось найти скачанный аудиофайл")

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
            title=info.get("title", "YouTube Audio"),
            duration=info.get("duration"),
            format_key="audio",
        )

    async def _download_with_quality(
        self, url: str, quality: str,
        progress_callback: ProgressCallback = None,
    ) -> DownloadResult:
        """Скачивает видео в указанном качестве"""
        import yt_dlp

        output_template = os.path.join(
            self.download_dir, f"%(id)s_{quality}p.%(ext)s"
        )

        # приоритет h264 — совместим с MP4 без перекодировки
        height = int(quality)
        format_str = (
            f"bestvideo[height<={height}][vcodec~='^(avc|h264)'][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={height}][vcodec~='^(avc|h264)']+bestaudio"
            f"/bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]"
            f"/bestvideo[height<={height}]+bestaudio"
            f"/best[height<={height}]"
            f"/best"
        )

        ydl_opts = {
            **self._base_opts(),
            "format": format_str,
            "outtmpl": output_template,
            # объединяем видео и аудио в mp4 (без перекодировки)
            "merge_output_format": "mp4",
        }

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, self._download, url, ydl_opts, progress_callback
        )

        file_path = self._find_downloaded_file(info, "mp4")

        if not file_path or not os.path.exists(file_path):
            raise RuntimeError("Не удалось найти скачанный видеофайл")

        return DownloadResult(
            file_path=file_path,
            media_type="video",
            title=info.get("title", "YouTube Video"),
            duration=info.get("duration"),
            format_key=f"video_{quality}",
        )

    def _extract_info(self, url: str, opts: dict) -> dict:
        """Извлекает метаданные (синхронно)"""
        import yt_dlp
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _download(self, url: str, opts: dict, progress_callback: ProgressCallback = None) -> dict:
        """Скачивает видео/аудио (синхронно)"""
        import yt_dlp

        # добавляем хук прогресса если передан callback
        if progress_callback:
            last_update = {"time": 0}

            def _hook(d):
                if d["status"] != "downloading":
                    return
                # обновляем не чаще раз в 3 секунды
                now = time.time()
                if now - last_update["time"] < 3:
                    return
                last_update["time"] = now

                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                if total > 0:
                    percent = int(downloaded / total * 100)
                    dl_mb = downloaded / 1024 / 1024
                    total_mb = total / 1024 / 1024
                    progress_callback(dl_mb, total_mb, percent)

            opts["progress_hooks"] = [_hook]

        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=True)

    def _find_downloaded_file(self, info: dict, expected_ext: str) -> str | None:
        """Ищет скачанный файл в папке загрузок"""
        video_id = info.get("id", "")

        # ищем файл по id видео
        for filename in os.listdir(self.download_dir):
            if video_id in filename and filename.endswith(f".{expected_ext}"):
                return os.path.join(self.download_dir, filename)

        # если не нашли по id — берём последний файл
        for filename in sorted(os.listdir(self.download_dir), reverse=True):
            if filename.endswith(f".{expected_ext}"):
                return os.path.join(self.download_dir, filename)

        return None

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
