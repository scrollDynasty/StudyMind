from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List
from PIL import Image
import pytesseract
import io
import os
import uuid
from pathlib import Path

router = APIRouter(prefix="/images", tags=["images"])

# Настройка пути к Tesseract для Windows
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

# Создаем абсолютный путь к папке uploads относительно корня проекта
BASE_DIR = Path(__file__).resolve().parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


async def save_image(file: UploadFile) -> Path:
    """Сохраняет загруженное изображение и возвращает путь"""
    filename = f"{uuid.uuid4()}{Path(file.filename).suffix}"
    filepath = UPLOAD_DIR / filename

    try:
        content = await file.read()
        with open(filepath, "wb") as f:
            f.write(content)
        return filepath
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла: {str(e)}")


def extract_text_from_image(image_path: Path) -> str:
    """Извлекает текст из изображения используя OCR"""
    try:
        # Открываем и предварительно обрабатываем изображение
        with Image.open(image_path) as img:
            # Конвертируем в RGB если изображение в другом формате
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Улучшаем качество распознавания
            text = pytesseract.image_to_string(
                img,
                lang='rus+eng',
                config='--psm 3 --oem 3'
            )

            if not text.strip():
                raise HTTPException(
                    status_code=400,
                    detail="Не удалось извлечь текст из изображения. Убедитесь, что изображение содержит четкий текст."
                )

            return text.strip()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при распознавании текста: {str(e)}"
        )


def generate_questions_from_text(text: str, num_questions: int = 5) -> List[dict]:
    """Генерирует вопросы на основе текста"""
    # Здесь должна быть ваша логика генерации вопросов
    # Пример простой реализации:
    sentences = [s.strip() for s in text.split('.') if s.strip()]
    questions = []

    for i, sentence in enumerate(sentences[:num_questions]):
        words = sentence.split()
        if len(words) < 3:
            continue

        # Выбираем случайное слово для замены
        import random
        word_idx = random.randint(0, len(words) - 1)
        correct_answer = words[word_idx]
        question_text = ' '.join(
            w if i != word_idx else "___"
            for i, w in enumerate(words)
        )

        # Генерируем варианты ответов
        options = [
            correct_answer,
            correct_answer.upper(),
            correct_answer.lower(),
            "не " + correct_answer.lower()
        ]
        random.shuffle(options)

        questions.append({
            "text": question_text,
            "options": options,
            "correct_answer": correct_answer
        })

    return questions


@router.post("/upload")
async def upload_images(
        files: List[UploadFile] = File(...),
        title: str = Form(...),
        num_questions: int = Form(5)
):
    """Загрузка изображений и генерация тестов"""
    if not files:
        raise HTTPException(status_code=400, detail="Не загружено ни одного файла")

    all_text = ""
    processed_files = []

    try:
        for file in files:
            if not file.content_type.startswith('image/'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Файл {file.filename} не является изображением"
                )

            # Сохраняем изображение
            filepath = await save_image(file)

            try:
                # Извлекаем текст
                text = extract_text_from_image(filepath)
                all_text += text + "\n\n"

                processed_files.append({
                    "filename": file.filename,
                    "text": text
                })

            finally:
                # Удаляем временный файл
                if filepath.exists():
                    filepath.unlink()

        if not all_text.strip():
            raise HTTPException(
                status_code=400,
                detail="Не удалось извлечь текст ни из одного изображения"
            )

        # Генерируем вопросы
        questions = generate_questions_from_text(all_text, num_questions)

        return {
            "test": {
                "title": title,
                "questions": questions,
                "processed_files": processed_files,  # Для отладки
                "extracted_text": all_text  # Для отладки
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке изображений: {str(e)}"
        )