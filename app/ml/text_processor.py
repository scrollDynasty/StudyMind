from typing import List
import re


class TextProcessor:
    def __init__(self):
        self.important_keywords = ['важно', 'ключевой', 'основной', 'определение', 'заключение']

    def process_text(self, text: str) -> dict:
        """
        Обработка текста без использования тяжелых ML моделей
        """
        paragraphs = text.split('\n')
        sentences = [s.strip() for p in paragraphs for s in p.split('.') if s.strip()]

        return {
            'sentences': len(sentences),
            'words': len(text.split()),
            'characters': len(text),
            'key_concepts': self.extract_key_concepts(text)
        }

    def extract_key_concepts(self, text: str) -> List[str]:
        """
        Простое извлечение ключевых концепций без использования ML
        """
        sentences = text.split('.')
        key_concepts = []

        for sentence in sentences:
            sentence = sentence.strip()
            # Ищем предложения с ключевыми словами
            if any(keyword in sentence.lower() for keyword in self.important_keywords):
                key_concepts.append(sentence)
            # Ищем определения (предложения с "- это" или "– это")
            elif re.search(r'.+[-–] это.+', sentence, re.IGNORECASE):
                key_concepts.append(sentence)

        return key_concepts

    def summarize(self, text: str, max_sentences: int = 3) -> str:
        """
        Простое суммирование текста
        """
        sentences = [s.strip() for s in text.split('.') if s.strip()]

        if len(sentences) <= max_sentences:
            return '. '.join(sentences) + '.'

        # Берем первое предложение
        summary = [sentences[0]]

        # Ищем предложения с ключевыми словами
        for sentence in sentences[1:-1]:
            if len(summary) < max_sentences - 1:
                if any(keyword in sentence.lower() for keyword in self.important_keywords):
                    summary.append(sentence)

        # Добавляем последнее предложение, если есть место
        if len(summary) < max_sentences:
            summary.append(sentences[-1])

        return '. '.join(summary) + '.'