"""Мультиязычность — русский, узбекский, английский
Использование: from bot.i18n import t
  t("start.welcome", lang="en", name="John")
"""

TRANSLATIONS = {
    # === /start ===
    "start.welcome": {
        "ru": (
            "👋 <b>Привет, {name}!</b>\n\n"
            "🎬 Я помогу тебе скачать видео и аудио с YouTube.\n\n"
            "📌 <b>Как пользоваться:</b>\n"
            "Просто отправь мне ссылку на видео — "
            "и я скачаю его для тебя! 🚀\n\n"
            "Выбери действие ниже:"
        ),
        "uz": (
            "👋 <b>Salom, {name}!</b>\n\n"
            "🎬 YouTube'dan video va audio yuklab olishda yordam beraman.\n\n"
            "📌 <b>Qanday foydalanish:</b>\n"
            "Menga video havolasini yuboring — "
            "men sizga yuklab beraman! 🚀\n\n"
            "Quyidagi tugmalardan birini tanlang:"
        ),
        "en": (
            "👋 <b>Hello, {name}!</b>\n\n"
            "🎬 I'll help you download videos and audio from YouTube.\n\n"
            "📌 <b>How to use:</b>\n"
            "Just send me a video link — "
            "and I'll download it for you! 🚀\n\n"
            "Choose an action below:"
        ),
    },

    # === Кнопки главного меню ===
    "btn.download": {
        "ru": "📥 Скачать видео",
        "uz": "📥 Video yuklab olish",
        "en": "📥 Download video",
    },
    "btn.profile": {
        "ru": "👤 Мой профиль",
        "uz": "👤 Mening profilim",
        "en": "👤 My profile",
    },
    "btn.help": {
        "ru": "❓ Помощь",
        "uz": "❓ Yordam",
        "en": "❓ Help",
    },
    "btn.back": {
        "ru": "◀️ Назад",
        "uz": "◀️ Orqaga",
        "en": "◀️ Back",
    },
    "btn.language": {
        "ru": "🌐 Сменить язык",
        "uz": "🌐 Tilni o'zgartirish",
        "en": "🌐 Change language",
    },

    # === Кнопки формата и качества ===
    "btn.format_video": {
        "ru": "🎬 Видео (MP4)",
        "uz": "🎬 Video (MP4)",
        "en": "🎬 Video (MP4)",
    },
    "btn.format_audio": {
        "ru": "🎵 Аудио (MP3)",
        "uz": "🎵 Audio (MP3)",
        "en": "🎵 Audio (MP3)",
    },
    "btn.download_audio_instead": {
        "ru": "🎵 Скачать аудио вместо видео",
        "uz": "🎵 Video o'rniga audio yuklab olish",
        "en": "🎵 Download audio instead",
    },

    # === Скачивание ===
    "download.prompt": {
        "ru": (
            "📥 <b>Скачивание с YouTube</b>\n\n"
            "Отправь мне ссылку на:\n"
            "• Видео\n"
            "• Shorts\n\n"
            "🔗 Пример: <code>https://www.youtube.com/watch?v=...</code>"
        ),
        "uz": (
            "📥 <b>YouTube'dan yuklab olish</b>\n\n"
            "Menga quyidagi havolani yuboring:\n"
            "• Video\n"
            "• Shorts\n\n"
            "🔗 Misol: <code>https://www.youtube.com/watch?v=...</code>"
        ),
        "en": (
            "📥 <b>Download from YouTube</b>\n\n"
            "Send me a link to:\n"
            "• Video\n"
            "• Shorts\n\n"
            "🔗 Example: <code>https://www.youtube.com/watch?v=...</code>"
        ),
    },
    "download.fetching_info": {
        "ru": "🔍 Получаю информацию о видео...",
        "uz": "🔍 Video haqida ma'lumot olinmoqda...",
        "en": "🔍 Fetching video info...",
    },
    "download.info": {
        "ru": (
            "📹 <b>{title}</b>\n\n"
            "⏱ Длительность: {duration}\n"
            "👤 Автор: {uploader}\n\n"
            "Выбери формат:"
        ),
        "uz": (
            "📹 <b>{title}</b>\n\n"
            "⏱ Davomiyligi: {duration}\n"
            "👤 Muallif: {uploader}\n\n"
            "Formatni tanlang:"
        ),
        "en": (
            "📹 <b>{title}</b>\n\n"
            "⏱ Duration: {duration}\n"
            "👤 Author: {uploader}\n\n"
            "Choose format:"
        ),
    },
    "download.choose_quality": {
        "ru": "📹 <b>Выбери качество видео:</b>",
        "uz": "📹 <b>Video sifatini tanlang:</b>",
        "en": "📹 <b>Choose video quality:</b>",
    },
    "download.processing": {
        "ru": "⏳ Скачиваю... Подожди немного",
        "uz": "⏳ Yuklab olinmoqda... Biroz kuting",
        "en": "⏳ Downloading... Please wait",
    },
    "download.quality_downgraded": {
        "ru": "⚠️ Видео в 720p оказалось больше 50 МБ — скачал в 360p.",
        "uz": "⚠️ 720p video 50 MB dan katta — 360p sifatda yuklandi.",
        "en": "⚠️ 720p video was over 50 MB — downloaded in 360p instead.",
    },
    "download.not_youtube": {
        "ru": (
            "🔎 Это не похоже на ссылку YouTube.\n\n"
            "Отправь ссылку вида:\n"
            "<code>https://www.youtube.com/watch?v=...</code>"
        ),
        "uz": (
            "🔎 Bu YouTube havolasiga o'xshamaydi.\n\n"
            "Quyidagi ko'rinishdagi havolani yuboring:\n"
            "<code>https://www.youtube.com/watch?v=...</code>"
        ),
        "en": (
            "🔎 This doesn't look like a YouTube link.\n\n"
            "Send a link like:\n"
            "<code>https://www.youtube.com/watch?v=...</code>"
        ),
    },

    # === Профиль ===
    "profile.title": {
        "ru": (
            "👤 <b>Твой профиль</b>\n\n"
            "✍️ Имя: {full_name}\n"
            "ℹ️ ID: <code>{user_id}</code>\n"
            "📥 Скачиваний: {downloads}\n"
        ),
        "uz": (
            "👤 <b>Sizning profilingiz</b>\n\n"
            "✍️ Ism: {full_name}\n"
            "ℹ️ ID: <code>{user_id}</code>\n"
            "📥 Yuklashlar: {downloads}\n"
        ),
        "en": (
            "👤 <b>Your profile</b>\n\n"
            "✍️ Name: {full_name}\n"
            "ℹ️ ID: <code>{user_id}</code>\n"
            "📥 Downloads: {downloads}\n"
        ),
    },

    # === Помощь ===
    "help.text": {
        "ru": (
            "📖 <b>Помощь</b>\n\n"
            "⭐ Отправь ссылку на YouTube видео — получишь файл\n"
            "⭐ Поддерживаются: видео, Shorts\n"
            "⭐ Можно скачать как видео (MP4) или аудио (MP3)\n"
            "🔒 Приватные видео не поддерживаются\n\n"
            "✈️ По вопросам: @{admin_username}"
        ),
        "uz": (
            "📖 <b>Yordam</b>\n\n"
            "⭐ YouTube video havolasini yuboring — faylni olasiz\n"
            "⭐ Qo'llab-quvvatlanadi: videolar, Shorts\n"
            "⭐ Video (MP4) yoki audio (MP3) sifatida yuklab olish mumkin\n"
            "🔒 Yopiq videolar qo'llab-quvvatlanmaydi\n\n"
            "✈️ Savollar uchun: @{admin_username}"
        ),
        "en": (
            "📖 <b>Help</b>\n\n"
            "⭐ Send a YouTube video link — get the file\n"
            "⭐ Supported: videos, Shorts\n"
            "⭐ Download as video (MP4) or audio (MP3)\n"
            "🔒 Private videos are not supported\n\n"
            "✈️ Contact: @{admin_username}"
        ),
    },

    # === Подписка ===
    "sub.welcome": {
        "ru": (
            "👋 <b>Привет!</b>\n\n"
            "🎬 Этот бот скачивает видео и аудио "
            "из YouTube — быстро и бесплатно!\n\n"
            "🔒 <b>Для начала подпишись на каналы ниже:</b>\n\n"
            "После подписки нажми «✅ Проверить подписку»"
        ),
        "uz": (
            "👋 <b>Salom!</b>\n\n"
            "🎬 Bu bot YouTube'dan video va audio "
            "yuklab oladi — tez va bepul!\n\n"
            "🔒 <b>Boshlash uchun quyidagi kanallarga obuna bo'ling:</b>\n\n"
            "Obuna bo'lgandan keyin «✅ Obunani tekshirish» tugmasini bosing"
        ),
        "en": (
            "👋 <b>Hello!</b>\n\n"
            "🎬 This bot downloads videos and audio "
            "from YouTube — fast and free!\n\n"
            "🔒 <b>To start, subscribe to the channels below:</b>\n\n"
            "After subscribing, tap «✅ Check subscription»"
        ),
    },
    "sub.not_subscribed": {
        "ru": (
            "❌ <b>Ты ещё не подписался на все каналы:</b>\n\n"
            "Подпишись и нажми «✅ Проверить подписку» ещё раз."
        ),
        "uz": (
            "❌ <b>Siz hali barcha kanallarga obuna bo'lmadingiz:</b>\n\n"
            "Obuna bo'ling va «✅ Obunani tekshirish» tugmasini qayta bosing."
        ),
        "en": (
            "❌ <b>You haven't subscribed to all channels yet:</b>\n\n"
            "Subscribe and tap «✅ Check subscription» again."
        ),
    },
    "sub.success": {
        "ru": (
            "✅ <b>Отлично, {name}!</b>\n\n"
            "Теперь ты можешь пользоваться ботом! 🚀\n\n"
            "Отправь ссылку на YouTube видео."
        ),
        "uz": (
            "✅ <b>Ajoyib, {name}!</b>\n\n"
            "Endi siz botdan foydalanishingiz mumkin! 🚀\n\n"
            "YouTube video havolasini yuboring."
        ),
        "en": (
            "✅ <b>Great, {name}!</b>\n\n"
            "You can now use the bot! 🚀\n\n"
            "Send a YouTube video link."
        ),
    },
    "btn.check_sub": {
        "ru": "✅ Проверить подписку",
        "uz": "✅ Obunani tekshirish",
        "en": "✅ Check subscription",
    },
    "sub.check_alert_fail": {
        "ru": "❌ Подпишись на все каналы!",
        "uz": "❌ Barcha kanallarga obuna bo'ling!",
        "en": "❌ Subscribe to all channels!",
    },
    "sub.check_alert_ok": {
        "ru": "✅ Подписка подтверждена!",
        "uz": "✅ Obuna tasdiqlandi!",
        "en": "✅ Subscription confirmed!",
    },
    "sub.not_required": {
        "ru": "✅ Подписка не требуется!",
        "uz": "✅ Obuna talab qilinmaydi!",
        "en": "✅ No subscription required!",
    },

    # === Ошибки ===
    "error.private": {
        "ru": "🔒 <b>Видео приватное</b>\n\nСкачивание приватных видео невозможно.",
        "uz": "🔒 <b>Video yopiq</b>\n\nYopiq videolarni yuklab olish mumkin emas.",
        "en": "🔒 <b>Private video</b>\n\nDownloading private videos is not possible.",
    },
    "error.not_found": {
        "ru": "❌ <b>Видео не найдено</b>\n\nВозможно, оно удалено или ссылка неправильная.",
        "uz": "❌ <b>Video topilmadi</b>\n\nEhtimol, u o'chirilgan yoki havola noto'g'ri.",
        "en": "❌ <b>Video not found</b>\n\nIt may have been deleted or the link is incorrect.",
    },
    "error.unavailable": {
        "ru": "❌ <b>Видео недоступно</b>\n\nВозможно, автор ограничил регион.",
        "uz": "❌ <b>Video mavjud emas</b>\n\nEhtimol, muallif mintaqani cheklagan.",
        "en": "❌ <b>Video unavailable</b>\n\nThe author may have restricted the region.",
    },
    "error.age_restricted": {
        "ru": "🔞 <b>Видео с ограничением по возрасту</b>\n\nК сожалению, такие видео нельзя скачать.",
        "uz": "🔞 <b>Yosh cheklovi bilan video</b>\n\nAfsuski, bunday videolarni yuklab olish mumkin emas.",
        "en": "🔞 <b>Age-restricted video</b>\n\nUnfortunately, these videos cannot be downloaded.",
    },
    "error.too_large": {
        "ru": "📦 <b>Файл слишком большой</b>\n\nTelegram ограничивает размер файла до 50 МБ.",
        "uz": "📦 <b>Fayl juda katta</b>\n\nTelegram fayl hajmini 50 MB bilan cheklaydi.",
        "en": "📦 <b>File too large</b>\n\nTelegram limits file size to 50 MB.",
    },
    "error.too_large_suggest_audio": {
        "ru": (
            "📦 <b>Видео слишком большое</b>\n\n"
            "Даже в 360p файл превышает 50 МБ.\n"
            "Попробуй скачать аудио:"
        ),
        "uz": (
            "📦 <b>Video juda katta</b>\n\n"
            "360p sifatda ham fayl 50 MB dan oshadi.\n"
            "Audio yuklab ko'ring:"
        ),
        "en": (
            "📦 <b>Video too large</b>\n\n"
            "Even at 360p the file exceeds 50 MB.\n"
            "Try downloading audio:"
        ),
    },
    "error.timeout": {
        "ru": "⏲ <b>Превышено время ожидания</b>\n\nПопробуй ещё раз через пару минут.",
        "uz": "⏲ <b>Kutish vaqti tugadi</b>\n\nBir necha daqiqadan keyin qayta urinib ko'ring.",
        "en": "⏲ <b>Request timed out</b>\n\nPlease try again in a few minutes.",
    },
    "error.generic": {
        "ru": "❌ <b>Не удалось скачать</b>\n\nПопробуй позже или проверь ссылку.",
        "uz": "❌ <b>Yuklab olib bo'lmadi</b>\n\nKeyinroq urinib ko'ring yoki havolani tekshiring.",
        "en": "❌ <b>Download failed</b>\n\nTry again later or check the link.",
    },
    "error.rate_limit": {
        "ru": "⏲ <b>Слишком много запросов!</b>\n\nПодожди {seconds} секунд и попробуй снова.",
        "uz": "⏲ <b>Juda ko'p so'rovlar!</b>\n\n{seconds} soniya kuting va qayta urinib ko'ring.",
        "en": "⏲ <b>Too many requests!</b>\n\nWait {seconds} seconds and try again.",
    },

    # === Выбор языка ===
    "lang.choose": {
        "ru": "🌐 <b>Выберите язык:</b>",
        "uz": "🌐 <b>Tilni tanlang:</b>",
        "en": "🌐 <b>Choose language:</b>",
    },
    "lang.changed": {
        "ru": "✅ Язык изменён на русский",
        "uz": "✅ Til o'zbek tiliga o'zgartirildi",
        "en": "✅ Language changed to English",
    },

    # === Админ-панель ===
    "admin.title": {
        "ru": "⚙️ <b>Админ-панель</b>\n\nВыбери действие:",
        "uz": "⚙️ <b>Admin panel</b>\n\nAmalni tanlang:",
        "en": "⚙️ <b>Admin panel</b>\n\nChoose an action:",
    },
    "admin.no_access": {
        "ru": "🔒 У тебя нет доступа к админке.",
        "uz": "🔒 Sizda admin panelga kirish huquqi yo'q.",
        "en": "🔒 You don't have access to admin panel.",
    },
    "admin.stats": {
        "ru": (
            "📈 <b>Статистика бота</b>\n\n"
            "👥 Всего юзеров: <b>{total_users}</b>\n"
            "⭐ Новых сегодня: <b>{today_users}</b>\n"
            "📥 Всего скачиваний: <b>{total_downloads}</b>\n"
            "📢 Каналов: <b>{total_channels}</b>"
        ),
        "uz": (
            "📈 <b>Bot statistikasi</b>\n\n"
            "👥 Jami foydalanuvchilar: <b>{total_users}</b>\n"
            "⭐ Bugungi yangi: <b>{today_users}</b>\n"
            "📥 Jami yuklashlar: <b>{total_downloads}</b>\n"
            "📢 Kanallar: <b>{total_channels}</b>"
        ),
        "en": (
            "📈 <b>Bot statistics</b>\n\n"
            "👥 Total users: <b>{total_users}</b>\n"
            "⭐ New today: <b>{today_users}</b>\n"
            "📥 Total downloads: <b>{total_downloads}</b>\n"
            "📢 Channels: <b>{total_channels}</b>"
        ),
    },
    "admin.channels_empty": {
        "ru": "📢 <b>Каналы</b>\n\nСписок пуст. Добавь канал кнопкой ниже.",
        "uz": "📢 <b>Kanallar</b>\n\nRo'yxat bo'sh. Quyidagi tugma orqali kanal qo'shing.",
        "en": "📢 <b>Channels</b>\n\nList is empty. Add a channel using the button below.",
    },
    "admin.channels_title": {
        "ru": "📢 <b>Каналы для подписки:</b>\n",
        "uz": "📢 <b>Obuna kanallari:</b>\n",
        "en": "📢 <b>Subscription channels:</b>\n",
    },
    "admin.add_channel_id": {
        "ru": (
            "📢 <b>Добавление канала</b>\n\n"
            "Отправь <b>ID канала</b> (например <code>-1001234567890</code>)\n\n"
            "💡 Узнать ID: добавь бота @getmyid_bot в канал"
        ),
        "uz": (
            "📢 <b>Kanal qo'shish</b>\n\n"
            "<b>Kanal ID</b> raqamini yuboring (masalan <code>-1001234567890</code>)\n\n"
            "💡 ID bilish: @getmyid_bot ni kanalga qo'shing"
        ),
        "en": (
            "📢 <b>Add channel</b>\n\n"
            "Send the <b>channel ID</b> (e.g. <code>-1001234567890</code>)\n\n"
            "💡 Get ID: add @getmyid_bot to the channel"
        ),
    },
    "admin.add_channel_title": {
        "ru": "✍️ Теперь отправь <b>название канала</b>:",
        "uz": "✍️ Endi <b>kanal nomini</b> yuboring:",
        "en": "✍️ Now send the <b>channel name</b>:",
    },
    "admin.add_channel_link": {
        "ru": (
            "🔗 Теперь отправь <b>ссылку или юзернейм канала</b>\n\n"
            "Принимаю любой формат:\n"
            "• <code>https://t.me/your_channel</code>\n"
            "• <code>@your_channel</code>\n"
            "• <code>your_channel</code>"
        ),
        "uz": (
            "🔗 Endi <b>kanal havolasi yoki username</b> yuboring\n\n"
            "Istalgan formatda:\n"
            "• <code>https://t.me/your_channel</code>\n"
            "• <code>@your_channel</code>\n"
            "• <code>your_channel</code>"
        ),
        "en": (
            "🔗 Now send the <b>channel link or username</b>\n\n"
            "Any format accepted:\n"
            "• <code>https://t.me/your_channel</code>\n"
            "• <code>@your_channel</code>\n"
            "• <code>your_channel</code>"
        ),
    },
    "admin.channel_added": {
        "ru": "✅ <b>Канал добавлен!</b>",
        "uz": "✅ <b>Kanal qo'shildi!</b>",
        "en": "✅ <b>Channel added!</b>",
    },
    "admin.confirm_delete": {
        "ru": "⚠️ <b>Удалить канал?</b>\n\nID: <code>{channel_id}</code>\n\nЭто действие нельзя отменить.",
        "uz": "⚠️ <b>Kanalni o'chirishni xohlaysizmi?</b>\n\nID: <code>{channel_id}</code>\n\nBu amalni qaytarib bo'lmaydi.",
        "en": "⚠️ <b>Delete channel?</b>\n\nID: <code>{channel_id}</code>\n\nThis action cannot be undone.",
    },
    "admin.id_not_number": {
        "ru": "❌ ID должен быть числом. Попробуй ещё раз:",
        "uz": "❌ ID raqam bo'lishi kerak. Qayta urinib ko'ring:",
        "en": "❌ ID must be a number. Try again:",
    },
    "admin.title_too_long": {
        "ru": "❌ Название слишком длинное (макс 200 символов)",
        "uz": "❌ Nom juda uzun (maks 200 belgi)",
        "en": "❌ Name is too long (max 200 characters)",
    },
    "admin.link_invalid": {
        "ru": "❌ Не удалось распознать ссылку.\nПопробуй ещё:",
        "uz": "❌ Havolani aniqlab bo'lmadi.\nQayta urinib ko'ring:",
        "en": "❌ Could not parse the link.\nTry again:",
    },

    # === Кнопки админки ===
    "btn.admin_stats": {"ru": "📊 Статистика", "uz": "📊 Statistika", "en": "📊 Statistics"},
    "btn.admin_channels": {"ru": "📢 Каналы", "uz": "📢 Kanallar", "en": "📢 Channels"},
    "btn.admin_home": {"ru": "🏠 Главное меню", "uz": "🏠 Bosh menyu", "en": "🏠 Main menu"},
    "btn.admin_add": {"ru": "➕ Добавить канал", "uz": "➕ Kanal qo'shish", "en": "➕ Add channel"},
    "btn.admin_back": {"ru": "◀️ Назад", "uz": "◀️ Orqaga", "en": "◀️ Back"},
    "btn.admin_cancel": {"ru": "❌ Отмена", "uz": "❌ Bekor qilish", "en": "❌ Cancel"},
    "btn.admin_confirm_del": {"ru": "✅ Да, удалить", "uz": "✅ Ha, o'chirish", "en": "✅ Yes, delete"},
    "btn.admin_cancel_del": {"ru": "❌ Отмена", "uz": "❌ Bekor qilish", "en": "❌ Cancel"},
    "btn.admin_panel": {"ru": "⚙️ Админ-панель", "uz": "⚙️ Admin panel", "en": "⚙️ Admin panel"},
    "btn.admin_broadcast": {"ru": "📨 Рассылка", "uz": "📨 Xabar yuborish", "en": "📨 Broadcast"},

    # === Рассылка ===
    "admin.broadcast_prompt": {
        "ru": "✈️ <b>Массовая рассылка</b>\n\nОтправь текст/фото/видео для рассылки.\nПоддерживается HTML.",
        "uz": "✈️ <b>Ommaviy xabar</b>\n\nYuborish uchun matn/rasm/video yuboring.\nHTML qo'llab-quvvatlanadi.",
        "en": "✈️ <b>Mass broadcast</b>\n\nSend text/photo/video to broadcast.\nHTML supported.",
    },
    "admin.broadcast_preview": {
        "ru": "👁 <b>Предпросмотр</b>\n\nОтправить это сообщение всем юзерам?",
        "uz": "👁 <b>Oldindan ko'rish</b>\n\nBu xabarni barcha foydalanuvchilarga yuborishni xohlaysizmi?",
        "en": "👁 <b>Preview</b>\n\nSend this message to all users?",
    },
    "admin.broadcast_confirm": {"ru": "✅ Да, отправить", "uz": "✅ Ha, yuborish", "en": "✅ Yes, send"},
    "admin.broadcast_cancel": {"ru": "❌ Отмена", "uz": "❌ Bekor qilish", "en": "❌ Cancel"},
    "admin.broadcast_started": {
        "ru": "✈️ Рассылка запущена... Ожидай отчёт.",
        "uz": "✈️ Xabar yuborilmoqda... Hisobotni kuting.",
        "en": "✈️ Broadcast started... Wait for report.",
    },
    "admin.broadcast_done": {
        "ru": "📈 <b>Рассылка завершена!</b>\n\n✅ Доставлено: <b>{success}</b>\n❌ Ошибок: <b>{failed}</b>\n👥 Всего: <b>{total}</b>",
        "uz": "📈 <b>Xabar yuborish tugadi!</b>\n\n✅ Yetkazildi: <b>{success}</b>\n❌ Xatolar: <b>{failed}</b>\n👥 Jami: <b>{total}</b>",
        "en": "📈 <b>Broadcast complete!</b>\n\n✅ Delivered: <b>{success}</b>\n❌ Failed: <b>{failed}</b>\n👥 Total: <b>{total}</b>",
    },
}


def t(key: str, lang: str = "ru", **kwargs) -> str:
    """Получить перевод по ключу и языку"""
    translations = TRANSLATIONS.get(key, {})
    text = translations.get(lang, translations.get("en", f"[{key}]"))
    if kwargs:
        text = text.format(**kwargs)
    return text


def detect_language(language_code: str | None) -> str:
    """Определяет язык по Telegram: ru → русский, uz → узбекский, остальное → английский"""
    if not language_code:
        return "en"
    if language_code.startswith("ru"):
        return "ru"
    if language_code.startswith("uz"):
        return "uz"
    return "en"
