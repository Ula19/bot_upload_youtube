"""Сервис скачивания YouTube — yt-dlp через Cloudflare WARP
WARP = бесплатный VPN, YouTube не блокирует IP Cloudflare.
Cookies не нужны — WARP обходит блокировку датацентровых IP.
Fallback: cookies → ios/android (если WARP упал).
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

# WARP SOCKS5 прокси (контейнер warp в docker-compose)
WARP_PROXY = "socks5://warp:9091"


@dataclass
class VideoInfo:
    """Информация о видео (до скачивания)"""
    title: str
    duration: int  # в секундах
    thumbnail: str | None = None
    uploader: str | None = None
    # доступные качества: {"360": 30, "720": 100} (качество → примерный размер в МБ)
    qualities: dict | None = None
    is_live: bool = False


@dataclass
class DownloadResult:
    """Результат скачивания"""
    file_path: str
    media_type: str       # video или audio
    title: str
    duration: int | None = None
    width: int | None = None
    height: int | None = None
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
    """Скачивает YouTube через yt-dlp + Cloudflare WARP.
    Основной метод — WARP (все качества без cookies).
    Fallback — cookies или ios/android.
    """

    _RATE_LIMIT_DELAY = 3
    _COOKIES_PATH = "/app/cookies/cookies.txt"

    def __init__(self):
        self.download_dir = tempfile.mkdtemp(prefix="yt_bot_")
        self._proxy = settings.proxy_url or None
        self._last_download_time = 0.0
        self.auth_failed = False

        logger.info("WARP прокси: %s", WARP_PROXY)
        if self._proxy:
            logger.info("Резидентный прокси (fallback): %s", self._proxy)

        if self.has_cookies():
            logger.info("Cookies: найдены (fallback)")
        else:
            logger.info("Cookies: не найдены")

    def has_cookies(self) -> bool:
        return os.path.isfile(self._COOKIES_PATH)

    async def _rate_limit(self):
        now = time.time()
        wait = self._RATE_LIMIT_DELAY - (now - self._last_download_time)
        if wait > 0:
            await asyncio.sleep(wait)
        self._last_download_time = time.time()

    def _cleanup_old_files(self, max_age_minutes: int = 30) -> None:
        now = time.time()
        cutoff = now - max_age_minutes * 60
        try:
            for filename in os.listdir(self.download_dir):
                filepath = os.path.join(self.download_dir, filename)
                if os.path.isfile(filepath) and os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
                    logger.info("Очистка старого файла: %s", filename)
        except OSError as e:
            logger.warning("Ошибка при очистке: %s", e)

    def _warp_opts(self) -> dict:
        """Настройки через WARP — все качества без cookies"""
        return {
            "quiet": True,
            "no_warnings": True,
            "proxy": WARP_PROXY,
            # увеличенные таймауты для WARP (SSL может тормозить)
            "socket_timeout": 30,
            "retries": 3,
        }

    def _cookies_opts(self) -> dict:
        """Fallback: cookies + WARP"""
        return {
            **self._warp_opts(),
            "cookiefile": self._COOKIES_PATH,
        }

    def _fallback_opts(self) -> dict:
        """Последний шанс: ios/android через WARP"""
        return {
            **self._warp_opts(),
            "extractor_args": {
                "youtube": {
                    "player_client": ["ios", "android"],
                },
            },
        }

    def _proxy_cookies_opts(self) -> dict:
        """Резидентный прокси + cookies (если WARP упал)"""
        opts = {
            "quiet": True,
            "no_warnings": True,
        }
        if self._proxy:
            opts["proxy"] = self._proxy
        opts["cookiefile"] = self._COOKIES_PATH
        return opts

    def _proxy_fallback_opts(self) -> dict:
        """Резидентный прокси + ios/android (если всё упало)"""
        opts = {
            "quiet": True,
            "no_warnings": True,
        }
        if self._proxy:
            opts["proxy"] = self._proxy
        opts["extractor_args"] = {
            "youtube": {
                "player_client": ["ios", "android"],
            },
        }
        return opts

    def _is_auth_error(self, error_msg: str) -> bool:
        return any(err in error_msg for err in _AUTH_ERRORS)

    async def get_info(self, url: str) -> VideoInfo:
        """Получает метаданные видео: WARP → прокси"""
        import yt_dlp

        t_start = time.monotonic()
        source = "warp"
        ydl_opts = {
            **self._warp_opts(),
            "skip_download": True,
            "ignore_no_formats_error": True,
        }

        loop = asyncio.get_event_loop()
        try:
            info = await loop.run_in_executor(
                None, self._extract_info, url, ydl_opts
            )
        except Exception as e:
            # WARP упал — пробуем через прокси
            if self._proxy:
                logger.warning("WARP не дал инфо, пробую прокси: %s", e)
                source = "proxy"
                fallback_opts = {
                    **self._proxy_fallback_opts(),
                    "skip_download": True,
                    "ignore_no_formats_error": True,
                }
                info = await loop.run_in_executor(
                    None, self._extract_info, url, fallback_opts
                )
            else:
                raise

        elapsed = time.monotonic() - t_start
        logger.info("[METRIC] get_info %.2fs source=%s url=%s", elapsed, source, url)

        qualities = self._parse_qualities(info)

        return VideoInfo(
            title=info.get("title", "Без названия"),
            duration=info.get("duration", 0),
            thumbnail=info.get("thumbnail"),
            uploader=info.get("uploader"),
            qualities=qualities,
            is_live=bool(info.get("is_live")),
        )

    def _parse_qualities(self, info: dict) -> dict:
        formats = info.get("formats", [])
        duration = info.get("duration", 0) or 0
        target_heights = [360, 480, 720, 1080, 1440]
        result = {}

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
                fmt_h = fmt.get("height") or 0
                fmt_w = fmt.get("width") or 0
                short_side = min(fmt_h, fmt_w) if fmt_w else fmt_h
                if short_side != h:
                    continue
                if fmt.get("vcodec", "none") == "none":
                    continue
                size = fmt.get("filesize") or fmt.get("filesize_approx") or 0
                if not size and fmt.get("tbr") and duration:
                    size = int(fmt["tbr"] * 1000 / 8 * duration)
                if size > best_size:
                    best_size = size

            if best_size > 0:
                total = best_size + audio_size
                total_mb = int(total / 1024 / 1024)
                result[str(h)] = max(total_mb, 1)

        if not result:
            result = {"360": 0, "720": 0}

        return result

    async def download_video(
        self, url: str, quality: str = "720",
        progress_callback: ProgressCallback = None,
    ) -> DownloadResult:
        """Скачивает видео: WARP → прокси+cookies → прокси+ios"""
        self._cleanup_old_files()
        await self._rate_limit()
        t_start = time.monotonic()

        # 1. WARP (основной — без cookies)
        try:
            result = await self._download_with_quality(
                url, quality, progress_callback, opts=self._warp_opts()
            )
            checked = self._check_size(result)
            self._log_download_metric("download_video", t_start, "warp", quality, checked.file_path)
            return checked
        except Exception as e:
            logger.warning("WARP не сработал: %s", e)

        # 2. резидентный прокси + cookies (если WARP упал)
        if self.has_cookies() and not self.auth_failed and self._proxy:
            try:
                logger.info("Fallback: резидентный прокси + cookies")
                result = await self._download_with_quality(
                    url, quality, progress_callback, opts=self._proxy_cookies_opts()
                )
                checked = self._check_size(result)
                self._log_download_metric("download_video", t_start, "proxy+cookies", quality, checked.file_path)
                return checked
            except Exception as e:
                if self._is_auth_error(str(e)):
                    self.auth_failed = True
                logger.warning("Прокси+cookies не сработали: %s", e)

        # 3. резидентный прокси + ios/android (последний шанс)
        if self._proxy:
            logger.info("Fallback: резидентный прокси + ios/android")
            result = await self._download_with_quality(
                url, quality, progress_callback, opts=self._proxy_fallback_opts()
            )
            checked = self._check_size(result)
            self._log_download_metric("download_video", t_start, "proxy+ios", quality, checked.file_path)
            return checked

        raise RuntimeError("Не удалось скачать видео: WARP недоступен, прокси не настроен")

    def _log_download_metric(
        self, op: str, t_start: float, source: str, quality: str, file_path: str
    ) -> None:
        elapsed = time.monotonic() - t_start
        try:
            size_mb = os.path.getsize(file_path) / 1024 / 1024
        except OSError:
            size_mb = 0
        speed = size_mb / elapsed if elapsed > 0 else 0
        logger.info(
            "[METRIC] %s %.2fs source=%s quality=%s size=%.1fMB speed=%.1fMB/s",
            op, elapsed, source, quality, size_mb, speed,
        )

    async def download_audio(
        self, url: str,
        progress_callback: ProgressCallback = None,
    ) -> DownloadResult:
        """Скачивает аудио: WARP → прокси+cookies → прокси+ios"""
        self._cleanup_old_files()
        await self._rate_limit()
        t_start = time.monotonic()

        # 1. WARP
        try:
            result = await self._do_download_audio(url, progress_callback, opts=self._warp_opts())
            self._log_download_metric("download_audio", t_start, "warp", "mp3", result.file_path)
            return result
        except Exception as e:
            logger.warning("WARP не сработал (аудио): %s", e)

        # 2. резидентный прокси + cookies
        if self.has_cookies() and not self.auth_failed and self._proxy:
            try:
                logger.info("Fallback: прокси + cookies (аудио)")
                result = await self._do_download_audio(url, progress_callback, opts=self._proxy_cookies_opts())
                self._log_download_metric("download_audio", t_start, "proxy+cookies", "mp3", result.file_path)
                return result
            except Exception as e:
                if self._is_auth_error(str(e)):
                    self.auth_failed = True
                logger.warning("Прокси+cookies не сработали (аудио): %s", e)

        # 3. резидентный прокси + ios/android
        if self._proxy:
            logger.info("Fallback: прокси + ios/android (аудио)")
            result = await self._do_download_audio(url, progress_callback, opts=self._proxy_fallback_opts())
            self._log_download_metric("download_audio", t_start, "proxy+ios", "mp3", result.file_path)
            return result

        raise RuntimeError("Не удалось скачать аудио: WARP недоступен, прокси не настроен")

    async def _do_download_audio(
        self, url: str, progress_callback: ProgressCallback, opts: dict,
    ) -> DownloadResult:
        import yt_dlp

        output_template = os.path.join(self.download_dir, "%(id)s_audio.%(ext)s")
        ydl_opts = {
            **opts,
            "format": "bestaudio[ext=m4a]/bestaudio/best",
            "outtmpl": output_template,
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
        opts: dict = None,
    ) -> DownloadResult:
        import yt_dlp

        output_template = os.path.join(self.download_dir, f"%(id)s_{quality}p.%(ext)s")
        height = int(quality)
        format_str = (
            f"bestvideo[height<={height}][vcodec~='^(avc|h264)']+bestaudio[ext=m4a]"
            f"/bestvideo[height<={height}]+bestaudio"
            f"/best[height<={height}]"
            f"/best"
        )

        ydl_opts = {
            **opts,
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
            width=info.get("width"),
            height=info.get("height"),
            format_key=f"video_{quality}",
        )

    def _extract_info(self, url: str, opts: dict) -> dict:
        import yt_dlp
        with yt_dlp.YoutubeDL(opts) as ydl:
            return ydl.extract_info(url, download=False)

    def _download(self, url: str, opts: dict, progress_callback: ProgressCallback = None) -> dict:
        import yt_dlp

        if progress_callback:
            last_update = {"time": 0}

            def _hook(d):
                if d["status"] != "downloading":
                    return
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
        video_id = info.get("id", "")
        for filename in os.listdir(self.download_dir):
            if video_id in filename and filename.endswith(f".{expected_ext}"):
                return os.path.join(self.download_dir, filename)
        for filename in sorted(os.listdir(self.download_dir), reverse=True):
            if filename.endswith(f".{expected_ext}"):
                return os.path.join(self.download_dir, filename)
        return None

    def cleanup(self, result: DownloadResult) -> None:
        self._remove_file(result.file_path)

    def _remove_file(self, path: str) -> None:
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info("Удалён: %s", path)
        except OSError as e:
            logger.warning("Не удалось удалить файл: %s", e)


class FileTooLargeError(Exception):
    pass


# глобальный экземпляр
downloader = YouTubeDownloader()
