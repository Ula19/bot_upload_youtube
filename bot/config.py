"""Конфигурация бота — все настройки из .env"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # токен бота
    bot_token: str

    # PostgreSQL
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "bot_4_youtube"
    db_user: str = "postgres"
    db_password: str = ""

    # админы бота (через запятую в .env)
    admin_ids: str = ""
    admin_username: str = "admin"

    # Telegram API (для Telethon — отправка файлов > 50 МБ)
    api_id: int = 0
    api_hash: str = ""

    # кэш скачиваний (дни)
    cache_ttl_days: int = 30

    # лимит файла для Telegram Bot API (в байтах)
    max_file_size: int = 50 * 1024 * 1024  # 50 МБ

    @property
    def telethon_enabled(self) -> bool:
        """Telethon включён если указаны api_id и api_hash"""
        return self.api_id > 0 and len(self.api_hash) > 0

    @property
    def admin_id_list(self) -> list[int]:
        """Парсит admin_ids из строки в список int"""
        if not self.admin_ids:
            return []
        return [int(x.strip()) for x in self.admin_ids.split(",") if x.strip()]

    @property
    def db_url(self) -> str:
        """URL для подключения к PostgreSQL через asyncpg"""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


# глобальный экземпляр настроек
settings = Settings()
