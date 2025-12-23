# -*- coding: utf-8 -*-
import os


class Config:
    # Секретный ключ для сессий (ИЗМЕНИТЕ ЭТО!)
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # База данных SQLite
    SQLALCHEMY_DATABASE_URI = 'sqlite:///tts_website.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Папка для аудиофайлов
    AUDIO_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "audio_files")

    # Папка для видеороликов
    VIDEO_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "video_files")

    # Папка для транскрибированных файлов
    TRANSCRIBE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "transcribe_files")

    # Максимальный размер файла для загрузки (100 МБ)
    MAX_CONTENT_LENGTH = 100 * 1024 * 1024

    # Максимальный размер текста
    MAX_TEXT_LENGTH = 5000

    # Стоимость в токенах (1 токен = 10 символов)
    CHARS_PER_TOKEN = 10

    # Админ по умолчанию (создается автоматически)
    DEFAULT_ADMIN_EMAIL = 'admin@example.com'
    DEFAULT_ADMIN_PASSWORD = 'admin123'  # ИЗМЕНИТЕ ПОСЛЕ ПЕРВОГО ВХОДА!

    # ====== Флаги включения/отключения функций ======
    # Если функция отключена, модуль не загружается и маршрут не регистрируется
    # Это снижает нагрузку на сервер и потребление памяти
    #
    # Примеры использования:
    # - Отключить транскрибацию: установите ENABLE_TRANSCRIBE = False
    # - Отключить через переменные окружения: export ENABLE_TRANSCRIBE=false
    # - Все функции включены по умолчанию (true)
    
    # TTS (Text-to-Speech) - конвертация текста в речь
    # Отключает: модуль edge_tts, маршрут /dashboard, форму TTSForm
    ENABLE_TTS = os.environ.get('ENABLE_TTS', 'true').lower() == 'true'
    
    # Скачивание видео с YouTube, TikTok, Reels
    # Отключает: модуль video_downloader, маршрут /video, форму VideoDownloadForm
    ENABLE_VIDEO_DOWNLOAD = os.environ.get('ENABLE_VIDEO_DOWNLOAD', 'true').lower() == 'true'
    
    # Транскрибация видео/аудио в текст
    # Отключает: модуль transcriber (whisper), маршрут /transcribe, форму TranscribeForm
    # ВАЖНО: Отключение этой функции значительно снижает потребление памяти
    ENABLE_TRANSCRIBE = os.environ.get('ENABLE_TRANSCRIBE', 'true').lower() == 'false'
    
    # Профиль пользователя
    # Отключает: маршрут /profile, форму ChangePasswordForm
    ENABLE_PROFILE = os.environ.get('ENABLE_PROFILE', 'true').lower() == 'true'
    
    # Тарифы
    # Отключает: маршрут /pricing
    ENABLE_PRICING = os.environ.get('ENABLE_PRICING', 'true').lower() == 'true'
    
    # Админ-панель
    # Отключает: маршрут /admin, формы GrantTokensForm и GrantAdminForm
    ENABLE_ADMIN = os.environ.get('ENABLE_ADMIN', 'true').lower() == 'true'