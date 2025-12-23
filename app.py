# -*- coding: utf-8 -*-
from flask import Flask, render_template, redirect, url_for, flash, request, send_file
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
import os
import asyncio
import re
from datetime import datetime

from config import Config
from models import db, User, Conversion, TokenTransaction
from forms import RegistrationForm, LoginForm

app = Flask(__name__)
app.config.from_object(Config)

# Условный импорт модулей и форм в зависимости от конфигурации
if app.config.get('ENABLE_TTS', True):
    from forms import TTSForm
    import edge_tts

if app.config.get('ENABLE_VIDEO_DOWNLOAD', True):
    from forms import VideoDownloadForm
    from video_downloader import downloader

if app.config.get('ENABLE_TRANSCRIBE', True):
    from forms import TranscribeForm
    from transcriber import transcriber

if app.config.get('ENABLE_ADMIN', True):
    from forms import GrantTokensForm, GrantAdminForm

if app.config.get('ENABLE_PROFILE', True):
    from forms import ChangePasswordForm

# Инициализация расширений
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@app.context_processor
def inject_config():
    """Делает конфиг доступным во всех шаблонах"""
    return dict(config=app.config)


def clean_text_for_tts(text):
    """Очистка текста для озвучки"""
    text = re.sub(r'\s+\.\s+', '. ', text)
    text = re.sub(r'\.{3,}', '...', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\.+$', '.', text.strip())
    return text.strip()


def calculate_tokens_needed(text_length):
    """Рассчитать необходимое количество токенов"""
    return (text_length + app.config['CHARS_PER_TOKEN'] - 1) // app.config['CHARS_PER_TOKEN']


async def generate_audio(text, voice, output_path):
    """Генерация аудио"""
    if not app.config.get('ENABLE_TTS', True):
        raise Exception('TTS функция отключена')
    import edge_tts
    communicate = edge_tts.Communicate(text, voice)
    await communicate.save(output_path)


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация пользователя"""
    if current_user.is_authenticated:
        # Редирект на первую доступную страницу
        if app.config.get('ENABLE_TTS', True):
            return redirect(url_for('dashboard'))
        elif app.config.get('ENABLE_VIDEO_DOWNLOAD', True):
            return redirect(url_for('video'))
        elif app.config.get('ENABLE_TRANSCRIBE', True):
            return redirect(url_for('transcribe'))
        else:
            return redirect(url_for('index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data)
        user.set_password(form.password.data)
        user.tokens = 100  # Бонусные токены при регистрации
        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Вам начислено 100 бонусных токенов.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в систему"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            next_page = request.args.get('next')
            flash(f'Добро пожаловать, {user.email}!', 'success')
            if next_page:
                return redirect(next_page)
            # Редирект на первую доступную страницу
            if app.config.get('ENABLE_TTS', True):
                return redirect(url_for('dashboard'))
            elif app.config.get('ENABLE_VIDEO_DOWNLOAD', True):
                return redirect(url_for('video'))
            elif app.config.get('ENABLE_TRANSCRIBE', True):
                return redirect(url_for('transcribe'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Неверный email или пароль', 'danger')

    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    """Панель пользователя"""
    if not app.config.get('ENABLE_TTS', True):
        flash('Функция TTS отключена', 'warning')
        return redirect(url_for('index'))
    
    from forms import TTSForm
    form = TTSForm()

    if form.validate_on_submit():
        text = clean_text_for_tts(form.text.data)
        text_length = len(text)
        tokens_needed = calculate_tokens_needed(text_length)

        if current_user.tokens < tokens_needed:
            flash(f'Недостаточно токенов! Нужно: {tokens_needed}, У вас: {current_user.tokens}', 'warning')
            return render_template('dashboard.html', form=form, user=current_user)

        try:
            # Генерация имени файла
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'audio_{current_user.id}_{timestamp}.mp3'
            filepath = os.path.join(app.config['AUDIO_FOLDER'], filename)

            # Создание аудио
            asyncio.run(generate_audio(text, form.voice.data, filepath))

            # Списание токенов
            current_user.use_tokens(tokens_needed)

            # Сохранение в историю
            conversion = Conversion(
                user_id=current_user.id,
                text_length=text_length,
                tokens_used=tokens_needed,
                voice_used=form.voice.data,
                filename=filename
            )
            db.session.add(conversion)

            # Запись транзакции
            transaction = TokenTransaction(
                user_id=current_user.id,
                amount=-tokens_needed,
                transaction_type='use',
                note=f'Конвертация текста ({text_length} символов)'
            )
            db.session.add(transaction)
            db.session.commit()

            flash(f'Аудио создано! Использовано {tokens_needed} токенов. Осталось: {current_user.tokens}', 'success')
            return send_file(filepath, as_attachment=True, download_name=filename)

        except Exception as e:
            flash(f'Ошибка при создании аудио: {str(e)}', 'danger')

    # История конвертаций
    conversions = current_user.conversions.order_by(Conversion.created_at.desc()).limit(10).all()

    return render_template('dashboard.html', form=form, user=current_user, conversions=conversions)


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    """Админ-панель"""
    if not app.config.get('ENABLE_ADMIN', True):
        flash('Админ-панель отключена', 'warning')
        return redirect(url_for('index'))
    
    if not current_user.is_admin:
        flash('Доступ запрещен', 'danger')
        return redirect(url_for('dashboard'))

    from forms import GrantTokensForm, GrantAdminForm
    form = GrantTokensForm()
    admin_form = GrantAdminForm()

    # Обработка выдачи админ-статуса (проверяем первым, так как у него меньше полей)
    if request.method == 'POST' and 'grant_admin' in request.form:
        if admin_form.validate():
            user = User.query.filter_by(email=admin_form.email.data).first()
            if user:
                if user.id == current_user.id:
                    flash('Нельзя изменить свой собственный статус', 'warning')
                else:
                    user.is_admin = True
                    db.session.commit()
                    flash(f'Пользователю {user.email} выдан админ-статус', 'success')
            else:
                flash('Пользователь не найден', 'danger')

    # Обработка выдачи токенов
    elif form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            user.add_tokens(form.tokens.data)

            # Запись транзакции
            transaction = TokenTransaction(
                user_id=user.id,
                admin_id=current_user.id,
                amount=form.tokens.data,
                transaction_type='grant',
                note=form.note.data or 'Выдано администратором'
            )
            db.session.add(transaction)
            db.session.commit()

            flash(f'Пользователю {user.email} выдано {form.tokens.data} токенов', 'success')
        else:
            flash('Пользователь не найден', 'danger')

    # Статистика
    users = User.query.all()
    total_users = len(users)
    total_conversions = Conversion.query.count()
    recent_transactions = TokenTransaction.query.order_by(TokenTransaction.created_at.desc()).limit(20).all()

    return render_template('admin.html',
                           form=form,
                           admin_form=admin_form,
                           users=users,
                           total_users=total_users,
                           total_conversions=total_conversions,
                           recent_transactions=recent_transactions)


def init_db():
    """Инициализация базы данных"""
    with app.app_context():
        db.create_all()

        # Создание админа по умолчанию
        admin = User.query.filter_by(email=app.config['DEFAULT_ADMIN_EMAIL']).first()
        if not admin:
            admin = User(
                email=app.config['DEFAULT_ADMIN_EMAIL'],
                is_admin=True,
                tokens=999999
            )
            admin.set_password(app.config['DEFAULT_ADMIN_PASSWORD'])
            db.session.add(admin)
            db.session.commit()
            print(f"✅ Создан админ: {app.config['DEFAULT_ADMIN_EMAIL']}")
            print(f"   Пароль: {app.config['DEFAULT_ADMIN_PASSWORD']}")
            print("   ⚠️ ИЗМЕНИТЕ ПАРОЛЬ ПОСЛЕ ПЕРВОГО ВХОДА!")

        # Создание папок для файлов (только если функции включены)
        if app.config.get('ENABLE_TTS', True):
            os.makedirs(app.config['AUDIO_FOLDER'], exist_ok=True)
        if app.config.get('ENABLE_VIDEO_DOWNLOAD', True):
            os.makedirs(app.config['VIDEO_FOLDER'], exist_ok=True)
        if app.config.get('ENABLE_TRANSCRIBE', True):
            os.makedirs(app.config['TRANSCRIBE_FOLDER'], exist_ok=True)


@app.route('/video', methods=['GET', 'POST'])
@login_required
def video():
    """Раздел скачивания видео"""
    if not app.config.get('ENABLE_VIDEO_DOWNLOAD', True):
        flash('Функция скачивания видео отключена', 'warning')
        return redirect(url_for('index'))
    
    from forms import VideoDownloadForm
    form = VideoDownloadForm()

    if form.validate_on_submit():
        url = form.url.data.strip()
        tokens_needed = 1

        if current_user.tokens < tokens_needed:
            flash(
                f'Недостаточно токенов! Нужно: {tokens_needed}, у вас: {current_user.tokens}',
                'warning',
            )
            return render_template('video.html', form=form, user=current_user)

        from video_downloader import VideoDownloader  # локальный импорт, чтобы избежать циклов

        platform = VideoDownloader.detect_platform(url)
        if not platform:
            flash('Не удалось определить платформу. Поддерживаются YouTube, TikTok и Reels.', 'danger')
            return render_template('video.html', form=form, user=current_user)

        try:
            filepath, title = asyncio.run(downloader.download_video(url, platform))

            current_user.use_tokens(tokens_needed)

            transaction = TokenTransaction(
                user_id=current_user.id,
                amount=-tokens_needed,
                transaction_type='use',
                note=f'Скачивание видео ({platform})',
            )
            db.session.add(transaction)
            db.session.commit()

            filename = os.path.basename(filepath)
            download_name = f'{title}.mp4' if not filename.lower().endswith('.mp4') else filename

            return send_file(filepath, as_attachment=True, download_name=download_name)
        except Exception as e:
            flash(f'Ошибка скачивания: {str(e)}', 'danger')

    return render_template('video.html', form=form, user=current_user)


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """Профиль пользователя"""
    if not app.config.get('ENABLE_PROFILE', True):
        flash('Функция профиля отключена', 'warning')
        return redirect(url_for('index'))
    
    from forms import ChangePasswordForm
    form = ChangePasswordForm()

    if form.validate_on_submit():
        if not current_user.check_password(form.current_password.data):
            flash('Неверный текущий пароль', 'danger')
        else:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            flash('Пароль успешно изменен', 'success')
            return redirect(url_for('profile'))

    return render_template('profile.html', form=form, user=current_user)


@app.route('/pricing')
def pricing():
    """Страница тарифов"""
    if not app.config.get('ENABLE_PRICING', True):
        flash('Страница тарифов отключена', 'warning')
        return redirect(url_for('index'))
    pricing_plans = [
        {
            'tokens': 100,
            'price': 5,
            'name': 'Базовый',
            'description': 'Идеально для начала работы',
            'popular': False
        },
        {
            'tokens': 500,
            'price': 15,
            'name': 'Стандартный',
            'description': 'Лучшее соотношение цены и качества',
            'popular': True
        },
        {
            'tokens': 1000,
            'price': 25,
            'name': 'Премиум',
            'description': 'Максимальная выгода для активных пользователей',
            'popular': False
        }
    ]
    return render_template('pricing.html', pricing_plans=pricing_plans)


@app.route('/transcribe', methods=['GET', 'POST'])
@login_required
def transcribe():
    """Страница транскрибации видео/аудио в текст"""
    if not app.config.get('ENABLE_TRANSCRIBE', True):
        flash('Функция транскрибации отключена', 'warning')
        return redirect(url_for('index'))
    
    from forms import TranscribeForm
    from transcriber import transcriber
    form = TranscribeForm()

    if form.validate_on_submit():
        file = form.file.data
        
        # Проверка расширения файла
        filename = file.filename.lower()
        if not (filename.endswith('.mp4') or filename.endswith('.mp3')):
            flash('Поддерживаются только файлы MP4 и MP3', 'danger')
            return render_template('transcribe.html', form=form, user=current_user)

        try:
            # Сохранение загруженного файла
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_ext = os.path.splitext(filename)[1]
            upload_filename = f'upload_{current_user.id}_{timestamp}{file_ext}'
            upload_path = os.path.join(app.config['TRANSCRIBE_FOLDER'], upload_filename)
            
            file.save(upload_path)

            # Получение длительности файла
            duration_seconds = transcriber.get_duration(upload_path)
            duration_minutes = duration_seconds / 60.0
            
            # Расчет токенов (1 минута = 10 токенов)
            tokens_needed = int(duration_minutes * 10)
            if tokens_needed < 1:
                tokens_needed = 1  # Минимум 1 токен

            if current_user.tokens < tokens_needed:
                os.remove(upload_path)  # Удаляем загруженный файл
                flash(
                    f'Недостаточно токенов! Нужно: {tokens_needed} токенов ({duration_minutes:.1f} мин), '
                    f'у вас: {current_user.tokens}',
                    'warning'
                )
                return render_template('transcribe.html', form=form, user=current_user)

            # Транскрибация с выбранным языком
            selected_language = form.language.data
            text, used_language = transcriber.transcribe(upload_path, language=selected_language)

            if not text:
                os.remove(upload_path)
                flash('Не удалось извлечь текст из файла. Возможно, в файле нет звука.', 'danger')
                return render_template('transcribe.html', form=form, user=current_user)

            # Сохранение текста в файл
            txt_filename = f'transcribe_{current_user.id}_{timestamp}.txt'
            txt_path = os.path.join(app.config['TRANSCRIBE_FOLDER'], txt_filename)
            
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)

            # Списание токенов
            current_user.use_tokens(tokens_needed)

            # Запись транзакции
            transaction = TokenTransaction(
                user_id=current_user.id,
                amount=-tokens_needed,
                transaction_type='use',
                note=f'Транскрибация ({duration_minutes:.1f} мин, {used_language})'
            )
            db.session.add(transaction)
            db.session.commit()

            # Удаление временного файла
            try:
                os.remove(upload_path)
            except:
                pass

            flash(
                f'Транскрибация завершена! Использовано {tokens_needed} токенов. '
                f'Язык: {used_language}. Осталось токенов: {current_user.tokens}',
                'success'
            )
            
            return send_file(txt_path, as_attachment=True, download_name=txt_filename)

        except Exception as e:
            # Удаление временного файла в случае ошибки
            try:
                if 'upload_path' in locals() and os.path.exists(upload_path):
                    os.remove(upload_path)
            except:
                pass
            
            flash(f'Ошибка транскрибации: {str(e)}', 'danger')

    return render_template('transcribe.html', form=form, user=current_user)


if __name__ == '__main__':
    init_db()
    print("🚀 Сервер запущен на http://127.0.0.1:5000")
    print(f"📧 Админ: {app.config['DEFAULT_ADMIN_EMAIL']}")
    app.run(debug=True, host='0.0.0.0', port=5000)