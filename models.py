# -*- coding: utf-8 -*-
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Модель пользователя"""
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    tokens = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Связь с историей конвертаций
    conversions = db.relationship('Conversion', backref='user', lazy='dynamic')

    def set_password(self, password):
        """Установить хэш пароля"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверить пароль"""
        return check_password_hash(self.password_hash, password)

    def add_tokens(self, amount):
        """Добавить токены"""
        self.tokens += amount
        db.session.commit()

    def use_tokens(self, amount):
        """Использовать токены"""
        if self.tokens >= amount:
            self.tokens -= amount
            db.session.commit()
            return True
        return False

    def __repr__(self):
        return f'<User {self.email}>'


class Conversion(db.Model):
    """История конвертаций текста в аудио"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text_length = db.Column(db.Integer, nullable=False)
    tokens_used = db.Column(db.Integer, nullable=False)
    voice_used = db.Column(db.String(100))
    filename = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Conversion {self.id} by User {self.user_id}>'


class TokenTransaction(db.Model):
    """История транзакций токенов"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    admin_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    amount = db.Column(db.Integer, nullable=False)
    transaction_type = db.Column(db.String(20))  # 'grant', 'use', 'revoke'
    note = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', foreign_keys=[user_id], backref='transactions')
    admin = db.relationship('User', foreign_keys=[admin_id])

    def __repr__(self):
        return f'<Transaction {self.id}: {self.amount} tokens>'