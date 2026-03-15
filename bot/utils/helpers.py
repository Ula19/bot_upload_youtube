"""Утилиты и вспомогательные функции"""
import re


# паттерны YouTube ссылок
_YOUTUBE_PATTERNS = [
    r"https?://(www\.)?youtube\.com/watch\?v=[\w\-]+",
    r"https?://(www\.)?youtube\.com/shorts/[\w\-]+",
    r"https?://youtu\.be/[\w\-]+",
    r"https?://(www\.)?youtube\.com/live/[\w\-]+",
    r"https?://m\.youtube\.com/watch\?v=[\w\-]+",
]


def is_youtube_url(text: str) -> bool:
    """Проверяет, является ли текст ссылкой на YouTube"""
    text = text.strip()
    return any(re.match(pattern, text) for pattern in _YOUTUBE_PATTERNS)


def clean_youtube_url(url: str) -> str:
    """Очищает URL — оставляет только ссылку с video id"""
    url = url.strip()

    # убираем лишние query-параметры, оставляем только v=
    if "youtube.com/watch" in url:
        match = re.search(r"[?&]v=([\w\-]+)", url)
        if match:
            return f"https://www.youtube.com/watch?v={match.group(1)}"

    # shorts — убираем query params
    if "youtube.com/shorts/" in url:
        match = re.search(r"shorts/([\w\-]+)", url)
        if match:
            return f"https://www.youtube.com/shorts/{match.group(1)}"

    # youtu.be — убираем query params
    if "youtu.be/" in url:
        match = re.search(r"youtu\.be/([\w\-]+)", url)
        if match:
            return f"https://youtu.be/{match.group(1)}"

    # на всякий случай — просто убираем query
    return url.split("?")[0].rstrip("/")


def extract_video_id(url: str) -> str | None:
    """Извлекает video ID из YouTube URL"""
    patterns = [
        r"(?:v=|/v/|youtu\.be/|/shorts/|/live/)([\w\-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
