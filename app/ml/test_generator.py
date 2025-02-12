from transformers import pipeline
from app.config import get_settings

settings = get_settings()

class TestGenerator:
    def __init__(self):
        self.qa_pipeline = pipeline("question-generation")

    def generate_questions(self, text: str, num_questions: int = 5):
        # Генерация вопросов на основе текста
        questions = self.qa_pipeline(text, max_questions=num_questions)
        return questions

    def evaluate_answer(self, question: str, correct_answer: str, user_answer: str):
        # Простая оценка ответа (можно улучшить с помощью более сложных методов)
        similarity = self.calculate_similarity(correct_answer.lower(), user_answer.lower())
        return {
            "score": similarity,
            "feedback": self.generate_feedback(similarity)
        }

    @staticmethod
    def calculate_similarity(text1: str, text2: str):
        # Простой пример расчета схожести (можно улучшить)
        words1 = set(text1.split())
        words2 = set(text2.split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    @staticmethod
    def generate_feedback(similarity_score: float):
        if similarity_score > 0.8:
            return "Отлично! Ответ правильный."
        elif similarity_score > 0.5:
            return "Хорошо, но можно улучшить. Попробуйте быть более точным."
        else:
            return "Попробуйте еще раз. Ответ не совсем верный."