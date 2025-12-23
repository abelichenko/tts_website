# -*- coding: utf-8 -*-
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError, URL
from models import User


class RegistrationForm(FlaskForm):
    """Форма регистрации"""
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обязателен'),
        Length(min=6, message='Пароль должен быть минимум 6 символов')
    ])
    password2 = PasswordField('Повторите пароль', validators=[
        DataRequired(message='Повторите пароль'),
        EqualTo('password', message='Пароли должны совпадать')
    ])

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Этот email уже зарегистрирован')


class LoginForm(FlaskForm):
    """Форма входа"""
    email = StringField('Email', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email')
    ])
    password = PasswordField('Пароль', validators=[
        DataRequired(message='Пароль обязателен')
    ])


class TTSForm(FlaskForm):
    """Форма конвертации текста в речь"""
    text = TextAreaField('Текст для озвучки', validators=[
        DataRequired(message='Введите текст'),
        Length(max=5000, message='Максимум 5000 символов')
    ])
    voice = SelectField('Голос', choices=[
        ('en-US-AriaNeural', '🇺🇸 Aria (US Female)'),
        ('en-US-GuyNeural', '🇺🇸 Guy (US Male)'),
        ('en-GB-SoniaNeural', '🇬🇧 Sonia (UK Female)'),
        ('en-GB-RyanNeural', '🇬🇧 Ryan (UK Male)'),
        ('ru-RU-SvetlanaNeural', '🇷🇺 Светлана (RU Female)'),
        ('ru-RU-DmitryNeural', '🇷🇺 Дмитрий (RU Male)'),
        ('uk-UA-PolinaNeural', '🇺🇦 Поліна (UA Female)'),
        ('uk-UA-OstapNeural', '🇺🇦 Остап (UA Male)'),
    ])


class GrantTokensForm(FlaskForm):
    """Форма выдачи токенов (для админа)"""
    email = StringField('Email пользователя', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email')
    ])
    tokens = IntegerField('Количество токенов', validators=[
        DataRequired(message='Укажите количество токенов')
    ])
    note = StringField('Примечание', validators=[Length(max=200)])


class VideoDownloadForm(FlaskForm):
    """Форма скачивания видео"""
    url = StringField(
        "Ссылка на видео (YouTube, TikTok, Reels)",
        validators=[
            DataRequired(message="Укажите ссылку на видео"),
            URL(message="Введите корректный URL"),
        ],
    )


class GrantAdminForm(FlaskForm):
    """Форма выдачи админ-статуса (для админа)"""
    email = StringField('Email пользователя', validators=[
        DataRequired(message='Email обязателен'),
        Email(message='Введите корректный email')
    ])


class ChangePasswordForm(FlaskForm):
    """Форма смены пароля"""
    current_password = PasswordField('Текущий пароль', validators=[
        DataRequired(message='Введите текущий пароль')
    ])
    new_password = PasswordField('Новый пароль', validators=[
        DataRequired(message='Введите новый пароль'),
        Length(min=6, message='Пароль должен быть минимум 6 символов')
    ])
    new_password2 = PasswordField('Повторите новый пароль', validators=[
        DataRequired(message='Повторите новый пароль'),
        EqualTo('new_password', message='Пароли должны совпадать')
    ])


class TranscribeForm(FlaskForm):
    """Форма транскрибации видео/аудио"""
    file = FileField(
        'Файл (MP4 или MP3)',
        validators=[
            FileRequired(message='Выберите файл для загрузки'),
            FileAllowed(['mp4', 'mp3'], message='Поддерживаются только файлы MP4 и MP3')
        ]
    )
    language = SelectField(
        'Язык',
        choices=[
            ('auto', 'Автоопределение'),
            ('en', '🇺🇸 Английский'),
            ('ru', '🇷🇺 Русский'),
            ('uk', '🇺🇦 Украинский'),
            ('de', '🇩🇪 Немецкий'),
            ('fr', '🇫🇷 Французский'),
            ('es', '🇪🇸 Испанский'),
            ('it', '🇮🇹 Итальянский'),
            ('pt', '🇵🇹 Португальский'),
            ('pl', '🇵🇱 Польский'),
            ('tr', '🇹🇷 Турецкий'),
            ('ar', '🇸🇦 Арабский'),
            ('zh', '🇨🇳 Китайский'),
            ('ja', '🇯🇵 Японский'),
            ('ko', '🇰🇷 Корейский'),
            ('hi', '🇮🇳 Хинди'),
            ('nl', '🇳🇱 Голландский'),
            ('sv', '🇸🇪 Шведский'),
            ('no', '🇳🇴 Норвежский'),
            ('da', '🇩🇰 Датский'),
            ('fi', '🇫🇮 Финский'),
            ('cs', '🇨🇿 Чешский'),
            ('hu', '🇭🇺 Венгерский'),
            ('ro', '🇷🇴 Румынский'),
            ('bg', '🇧🇬 Болгарский'),
            ('hr', '🇭🇷 Хорватский'),
            ('sk', '🇸🇰 Словацкий'),
            ('sl', '🇸🇮 Словенский'),
            ('et', '🇪🇪 Эстонский'),
            ('lv', '🇱🇻 Латышский'),
            ('lt', '🇱🇹 Литовский'),
            ('el', '🇬🇷 Греческий'),
            ('he', '🇮🇱 Иврит'),
            ('th', '🇹🇭 Тайский'),
            ('vi', '🇻🇳 Вьетнамский'),
            ('id', '🇮🇩 Индонезийский'),
            ('ms', '🇲🇾 Малайский'),
        ],
        default='auto',
        validators=[DataRequired(message='Выберите язык')]
    )
