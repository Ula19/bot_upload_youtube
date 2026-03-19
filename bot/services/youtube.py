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
    # доступные качества: {"360": 30, "720": 100} (качество → примерный размер в МБ)
    qualities: dict | None = None


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


# ошибки при которых cookies протухли → fallback на ios/android
_AUTH_ERRORS = [
    "Sign in to confirm",
    "confirm you're not a bot",
    "This request was detected as a bot",
    "Login required",
    "cookies",
]


class YouTubeDownloader:
    """Скачивает YouTube через yt-dlp.
    Основной метод — cookies (720p), fallback — ios/android (360p).
    """

    _RATE_LIMIT_DELAY = 3
    # путь к cookies файлу (volume в docker-compose)
    _COOKIES_PATH = "/app/cookies/cookies.txt"

    def __init__(self):
        self.download_dir = tempfile.mkdtemp(prefix="yt_bot_")
        self._proxy = settings.proxy_url or None
        self._last_download_time = 0.0
        # флаг: cookies протухли → уведомить админа (один раз)
        self.auth_failed = False

        if self._proxy:
            logger.info("Прокси подключен: %s", self._proxy)
        else:
            logger.warning("Прокси не настроен — YouTube может блокировать")

        if self.has_cookies():
            logger.info("Cookies: найдены → 720p")
        else:
            logger.info("Cookies: не найдены → только ios/android (360p)")

    def has_cookies(self) -> bool:
        """Есть ли cookies файл?"""
        return os.path.isfile(self._COOKIES_PATH)

    async def _rate_limit(self):
        """Ждём между запросами чтобы YouTube не заблокировал"""
        now = time.time()
        wait = self._RATE_LIMIT_DELAY - (now - self._last_download_time)
        if wait > 0:
            logger.info("Пауза %.1f сек (rate-limit)", wait)
            await asyncio.sleep(wait)
        self._last_download_time = time.time()

    def _common_opts(self) -> dict:
        """Общие настройки для всех запросов"""
        opts = {
            "quiet": True,
            "no_warnings": True,
            # JS challenge solver для deno (нужен для 720p DASH-форматов)
            "remote_components": {"ejs": "github"},
        }
        if self._proxy:
            opts["proxy"] = self._proxy
        return opts

    def _auth_opts(self) -> dict:
        """Настройки с cookies — полные форматы (720p+ h264)"""
        return {
            **self._common_opts(),
            "cookiefile": self._COOKIES_PATH,
        }

    def _fallback_opts(self) -> dict:
        """Настройки без аккаунта — ios/android клиент (360-480p)"""
        return {
            **self._common_opts(),
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android"],
                },
            },
        }

    def _is_auth_error(self, error_msg: str) -> bool:
        """Проверяет — это ошибка авторизации?"""
        return any(err in error_msg for err in _AUTH_ERRORS)

    async def get_info(self, url: str) -> VideoInfo:
        """Получает метаданные видео + доступные качества с размерами"""
        import yt_dlp

        # используем cookies если есть — покажет все качества (720p+)
        base = self._auth_opts() if self.has_cookies() else self._fallback_opts()
        ydl_opts = {
            **base,
            "skip_download": True,
            "ignore_no_formats_error": True,
        }

        loop = asyncio.get_event_loop()
        info = await loop.run_in_executor(
            None, self._extract_info, url, ydl_opts
        )

        # парсим доступные качества из форматов
        qualities = self._parse_qualities(info)

        return VideoInfo(
            title=info.get("title", "Без названия"),
            duration=info.get("duration", 0),
            thumbnail=info.get("thumbnail"),
            uploader=info.get("uploader"),
            qualities=qualities,
        )

    def _parse_qualities(self, info: dict) -> dict:
        """Парсит форматы и возвращает доступные качества с примерным размером"""
        formats = info.get("formats", [])
        duration = info.get("duration", 0) or 0
        # все нужные качества
        target_heights = [360, 480, 720, 1080]
        result = {}

        # находим лучший аудио-поток (для DASH нужно прибавить его размер)
        audio_size = 0
        for fmt in formats:
            if fmt.get("vcodec", "none") != "none":
                continue
            if fmt.get("acodec", "none") == "none":
                continue
            size = fmt.get("filesize") or fmt.get("filesize_approx") or 0
            if not size and fmt.get("tbr") and duration:
                size = int(fmt["tbr"] * 1000 / 8 * duration)
            if size > audio_size:
                audio_size = size

        for h in target_heights:
            best_size = 0
            for fmt in formats:
                height = fmt.get("height") or 0
                if height != h:
                    continue
                if fmt.get("vcodec", "none") == "none":
                    continue
                size = fmt.get("filesize") or fmt.get("filesize_approx") or 0
                if not size and fmt.get("tbr") and duration:
                    size = int(fmt["tbr"] * 1000 / 8 * duration)
                if size > best_size:
                    best_size = size

            if best_size > 0:
                # прибавляем аудио-дорожку
                total = best_size + audio_size
                total_mb = int(total / 1024 / 1024)
                result[str(h)] = max(total_mb, 1)

        # если ничего не нашли — даём дефолтные кнопки
        if not result:
            result = {"360": 0, "720": 0}

        return result

    async def download_video(
        self, url: str, quality: str = "720",
        progress_callback: ProgressCallback = None,
    ) -> DownloadResult:
        """Скачивает видео: cookies (720p) → fallback ios/android (360p)"""
        await self._rate_limit()

        # пробуем через cookies (если есть и не протухли)
        if self.has_cookies() and not self.auth_failed:
            try:
                result = await self._download_with_quality(
                    url, quality, progress_callback, use_auth=True
                )
                return self._check_size(result)
            except Exception as e:
                if self._is_auth_error(str(e)):
                    self.auth_failed = True  # постоянный fallback
                logger.warning("Cookies не сработали, fallback: %s", e)

        # fallback — ios/android без аккаунта
        logger.info("Скачиваю через ios/android")
        result = await self._download_with_quality(
            url, quality, progress_callback, use_auth=False
        )
        return self._check_size(result)

    async def download_audio(
        self, url: str,
        progress_callback: ProgressCallback = None,
    ) -> DownloadResult:
        """Скачивает аудио: cookies → fallback ios/android"""
        await self._rate_limit()

        if self.has_cookies() and not self.auth_failed:
            try:
                return await self._do_download_audio(url, progress_callback, use_auth=True)
            except Exception as e:
                if self._is_auth_error(str(e)):
                    self.auth_failed = True
                logger.warning("Cookies не сработали (аудио), fallback: %s", e)

        return await self._do_download_audio(url, progress_callback, use_auth=False)

    async def _do_download_audio(
        self, url: str, progress_callback: ProgressCallback, use_auth: bool,
    ) -> DownloadResult:
        """Скачивает аудио с выбранными настройками"""
        import yt_dlp

        base = self._auth_opts() if use_auth else self._fallback_opts()
        output_template = os.path.join(
            self.download_dir, "%(id)s_audio.%(ext)s"
        )

        ydl_opts = {
            **base,
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

        file_path = self._find_downloaded_file(info, "mp3")
        if not file_path or not os.path.exists(file_path):
            raise RuntimeError("Не удалось найти скачанный аудиофайл")

        return self._check_size(DownloadResult(
            file_path=file_path,
            media_type="audio",
            title=info.get("title", "YouTube Audio"),
            duration=info.get("duration"),
            format_key="audio",
        ))

    def _check_size(self, result: DownloadResult) -> DownloadResult:
        """Проверяет что файл не превышает лимит Telegram"""
        file_size = os.path.getsize(result.file_path)
        if file_size > MAX_FILE_SIZE:
            self._remove_file(result.file_path)
            raise FileTooLargeError(
                f"Файл слишком большой ({file_size / 1024 / 1024:.0f} МБ)"
            )
        return result

    async def _download_with_quality(
        self, url: str, quality: str,
        progress_callback: ProgressCallback = None,
        use_auth: bool = True,
    ) -> DownloadResult:
        """Скачивает видео в указанном качестве"""
        import yt_dlp

        base = self._auth_opts() if use_auth else self._fallback_opts()
        output_template = os.path.join(
            self.download_dir, f"%(id)s_{quality}p.%(ext)s"
        )

        height = int(quality)
        # универсальный format_str: сначала h264, потом любой кодек
        format_str = (
            f"bestvideo[height<={height}][vcodec~='^(avc|h264)']+bestaudio[ext=m4a]"
            f"/bestvideo[height<={height}]+bestaudio"
            f"/best[height<={height}]"
            f"/best"
        )

        ydl_opts = {
            **base,
            "format": format_str,
            "outtmpl": output_template,
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
