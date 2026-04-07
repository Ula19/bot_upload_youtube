"""Обработчик /update_cookies — обновление cookies для YouTube
Только для админов: отправляют файл cookies.txt → бот сохраняет
"""
import logging
import os
import shutil

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.config import settings
from bot.emojis import E

logger = logging.getLogger(__name__)
router = Router()

# путь куда сохраняем cookies
COOKIES_DIR = "/app/cookies"
COOKIES_PATH = os.path.join(COOKIES_DIR, "cookies.txt")


class CookiesStates(StatesGroup):
    """FSM для загрузки cookies"""
    waiting_file = State()


@router.message(F.text == "/update_cookies")
async def cmd_update_cookies(message: Message, state: FSMContext) -> None:
    """Команда /update_cookies — начинаем процесс обновления"""
    # только админы могут обновлять cookies
    if message.from_user.id not in settings.admin_id_list:
        await message.answer(f"{E['ban']} Только администратор может обновить cookies.")
        return

    await state.set_state(CookiesStates.waiting_file)
    await message.answer(
        f"{E['folder']} <b>Отправьте файл cookies.txt</b>\n\n"
        "Как получить:\n"
        '1. Откройте Firefox в <b>приватном</b> режиме\n'
        '2. Войдите в <a href="https://youtube.com">YouTube</a>\n'
        '3. Установите расширение "Get cookies.txt LOCALLY"\n'
        '4. Экспортируйте cookies и отправьте файл сюда\n'
        '5. <b>Сразу закройте</b> приватное окно!\n\n'
        "Отмена: /cancel",
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


@router.message(CookiesStates.waiting_file, F.document)
async def process_cookies_file(message: Message, state: FSMContext) -> None:
    """Получили файл — сохраняем как cookies.txt"""
    doc = message.document

    # проверяем что это текстовый файл
    if doc.file_size > 1_000_000:  # 1 МБ макс
        await message.answer(f"{E['cross']} Файл слишком большой. cookies.txt обычно < 100 КБ")
        return

    try:
        # создаём папку если нет
        os.makedirs(COOKIES_DIR, exist_ok=True)

        # с Local Bot API файл уже на диске → просто копируем
        file = await message.bot.get_file(doc.file_id)
        local_path = file.file_path  # путь типа /var/lib/telegram-bot-api/.../file.txt
        if os.path.isfile(local_path):
            shutil.copy2(local_path, COOKIES_PATH)
        else:
            # обычный Bot API — скачиваем
            await message.bot.download_file(file.file_path, COOKIES_PATH)

        # проверяем что файл валидный (содержит нужные строки)
        with open(COOKIES_PATH, "r") as f:
            content = f.read()
        if ".youtube.com" not in content:
            await message.answer(
                f"{E['warning']} Файл сохранён, но не похож на YouTube cookies.\n"
                "Убедитесь что вы экспортировали cookies с youtube.com"
            )
        else:
            await message.answer(
                f"{E['check']} <b>Cookies обновлены!</b>\n\n"
                "Теперь видео будет скачиваться в 720p+ качестве.\n"
                "Cookies обычно живут 2-4 недели.",
                parse_mode="HTML",
            )
            logger.info("Cookies обновлены пользователем %s", message.from_user.id)

    except Exception as e:
        logger.error("Ошибка сохранения cookies: %s", e)
        await message.answer(f"{E['cross']} Ошибка: {e}")
    finally:
        await state.clear()


@router.message(CookiesStates.waiting_file)
async def process_cookies_not_file(message: Message) -> None:
    """Юзер отправил не файл"""
    if message.text and message.text.startswith("/cancel"):
        return
    await message.answer(f"{E['folder']} Отправьте именно <b>файл</b> cookies.txt", parse_mode="HTML")
