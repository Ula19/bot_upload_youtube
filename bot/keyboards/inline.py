"""Inline-клавиатуры — меню, подписка, формат, качество"""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import settings
from bot.i18n import t


def get_start_keyboard(user_id: int, lang: str = "ru") -> InlineKeyboardMarkup:
    """Главное меню бота"""
    buttons = [
        [InlineKeyboardButton(
            text=t("btn.download", lang),
            callback_data="download_video",
        )],
        [
            InlineKeyboardButton(
                text=t("btn.profile", lang),
                callback_data="my_profile",
            ),
            InlineKeyboardButton(
                text=t("btn.help", lang),
                callback_data="help",
            ),
        ],
        [InlineKeyboardButton(
            text=t("btn.language", lang),
            callback_data="change_language",
        )],
    ]

    # кнопка админки для админов
    if user_id in settings.admin_id_list:
        buttons.append([InlineKeyboardButton(
            text=t("btn.admin_panel", lang),
            callback_data="admin_panel",
        )])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_back_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Кнопка 'Назад' в главное меню"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("btn.back", lang),
            callback_data="back_to_menu",
        )],
    ])


def get_format_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Выбор формата: видео или аудио"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=t("btn.format_video", lang),
                callback_data="fmt_video",
            ),
            InlineKeyboardButton(
                text=t("btn.format_audio", lang),
                callback_data="fmt_audio",
            ),
        ],
        [InlineKeyboardButton(
            text=t("btn.back", lang),
            callback_data="back_to_menu",
        )],
    ])


def get_quality_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Выбор качества видео"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📹 360p",
                callback_data="quality_360",
            ),
            InlineKeyboardButton(
                text="📹 720p",
                callback_data="quality_720",
            ),
        ],
        [InlineKeyboardButton(
            text=t("btn.back", lang),
            callback_data="back_to_menu",
        )],
    ])


def get_audio_suggest_keyboard(lang: str = "ru") -> InlineKeyboardMarkup:
    """Предложение скачать аудио (когда видео слишком большое)"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=t("btn.download_audio_instead", lang),
            callback_data="fmt_audio",
        )],
        [InlineKeyboardButton(
            text=t("btn.back", lang),
            callback_data="back_to_menu",
        )],
    ])


def get_subscription_keyboard(
    channels: list[dict], lang: str = "ru"
) -> InlineKeyboardMarkup:
    """Клавиатура подписки на каналы"""
    buttons = []
    for ch in channels:
        buttons.append([InlineKeyboardButton(
            text=f"📢 {ch['title']}",
            url=ch["invite_link"],
        )])
    buttons.append([InlineKeyboardButton(
        text=t("btn.check_sub", lang),
        callback_data="check_subscription",
    )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_lang_ru"),
            InlineKeyboardButton(text="🇺🇿 O'zbek", callback_data="set_lang_uz"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="set_lang_en"),
        ],
    ])
