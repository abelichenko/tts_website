# -*- coding: utf-8 -*-
import whisper
import os
from pydub import AudioSegment
import torch


class Transcriber:
    """Класс для транскрибации видео и аудио файлов"""
    
    def __init__(self):
        # Используем модель 'small' - лучший баланс точности и скорости
        # 'small' дает значительно лучшую точность чем 'base', но не так тяжелая как 'medium'
        # Если нужна максимальная точность - можно использовать 'medium' или 'large'
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model = whisper.load_model("small", device=self.device)
        print(f"✅ Whisper модель 'small' загружена на устройство: {self.device}")
    
    def get_duration(self, filepath: str) -> float:
        """Получить длительность файла в секундах (оптимизированный метод)"""
        try:
            # Используем pydub - это быстрее и легче чем полная транскрибация
            # pydub использует ffprobe под капотом, что очень эффективно
            if filepath.lower().endswith('.mp3'):
                audio = AudioSegment.from_mp3(filepath)
            elif filepath.lower().endswith('.mp4'):
                # Для MP4 извлекаем только метаданные, не весь файл
                audio = AudioSegment.from_file(filepath, format="mp4")
            else:
                audio = AudioSegment.from_file(filepath)
            
            # Длительность в секундах
            duration_seconds = len(audio) / 1000.0
            return duration_seconds
            
        except Exception as e:
            raise Exception(f"Ошибка определения длительности: {str(e)}")
    
    def transcribe(self, filepath: str, language: str = 'auto') -> tuple[str, str]:
        """
        Транскрибировать файл
        
        Args:
            filepath: Путь к файлу
            language: Код языка ('auto' для автоопределения, или код языка, например 'ru', 'en')
        
        Returns:
            tuple: (текст, используемый_язык)
        """
        try:
            # Маппинг кодов языков на читаемые названия
            language_map = {
                'en': 'Английский',
                'ru': 'Русский',
                'uk': 'Украинский',
                'de': 'Немецкий',
                'fr': 'Французский',
                'es': 'Испанский',
                'it': 'Итальянский',
                'pt': 'Португальский',
                'ja': 'Японский',
                'ko': 'Корейский',
                'zh': 'Китайский',
                'ar': 'Арабский',
                'tr': 'Турецкий',
                'pl': 'Польский',
                'nl': 'Голландский',
                'sv': 'Шведский',
                'no': 'Норвежский',
                'da': 'Датский',
                'fi': 'Финский',
                'cs': 'Чешский',
                'hu': 'Венгерский',
                'ro': 'Румынский',
                'bg': 'Болгарский',
                'hr': 'Хорватский',
                'sk': 'Словацкий',
                'sl': 'Словенский',
                'et': 'Эстонский',
                'lv': 'Латышский',
                'lt': 'Литовский',
                'el': 'Греческий',
                'he': 'Иврит',
                'hi': 'Хинди',
                'th': 'Тайский',
                'vi': 'Вьетнамский',
                'id': 'Индонезийский',
                'ms': 'Малайский',
                'tl': 'Тагальский',
            }
            
            # Оптимизированные параметры для лучшей точности и производительности
            transcribe_options = {
                'verbose': False,
                'fp16': (self.device == "cuda"),  # Используем fp16 на CUDA для скорости, float32 на CPU для точности
                'temperature': 0.0,  # Детерминированный вывод для лучшей точности
                'compression_ratio_threshold': 2.4,  # Фильтр для низкокачественных сегментов
                'logprob_threshold': -1.0,  # Порог вероятности для фильтрации
                'no_speech_threshold': 0.6,  # Порог для определения отсутствия речи
                'condition_on_previous_text': True,  # Использовать контекст предыдущего текста (улучшает точность)
                'word_timestamps': False,  # Отключаем для экономии ресурсов
                'initial_prompt': None,  # Можно добавить подсказку для улучшения точности
            }
            
            # Если язык не указан или 'auto', Whisper определит автоматически
            if language == 'auto' or not language:
                result = self.model.transcribe(filepath, **transcribe_options)
                detected_language = result.get('language', 'unknown')
                language_name = language_map.get(detected_language, detected_language.upper())
            else:
                # Используем указанный язык - это улучшает точность
                transcribe_options['language'] = language
                result = self.model.transcribe(filepath, **transcribe_options)
                language_name = language_map.get(language, language.upper())
            
            # Извлекаем весь текст из всех сегментов для максимальной полноты
            text = result.get('text', '').strip()
            
            # Дополнительно: собираем текст из всех сегментов если есть
            if 'segments' in result and result['segments']:
                segments_text = ' '.join([seg.get('text', '').strip() for seg in result['segments'] if seg.get('text')])
                # Используем более полный вариант если он длиннее
                if len(segments_text) > len(text):
                    text = segments_text.strip()
            
            # Очистка текста: удаляем лишние пробелы, но сохраняем структуру
            text = ' '.join(text.split())  # Нормализация пробелов
            
            return text, language_name
            
        except Exception as e:
            raise Exception(f"Ошибка транскрибации: {str(e)}")


# Глобальный экземпляр транскрибера
transcriber = Transcriber()

