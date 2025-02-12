from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import List
from PIL import Image
import pytesseract
import io
import os
import uuid
from app.ml.text_processor import TextProcessor
from app.routers.tests import generate_questions_from_text

# Настройка пути к Tesseract (для Windows)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

router = APIRouter(prefix="/images", tags=["images"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def save_image(file: UploadFile) -> str:
    filename = f"{uuid.uuid4()}{os.path.splitext(file.filename)[1]}"
    filepath = os.path.join(UPLOAD_DIR, filename)

    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)

    return filepath


def extract_text_from_image(image_path: str) -> str:
    try:
        img = Image.open(image_path)
        # Улучшаем качество распознавания
        text = pytesseract.image_to_string(
            img,
            lang='rus+eng',
            config='--psm 3 --oem 3'  # Используем нейронную сеть и авто-определение ориентации
        )
        return text.strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при распознавании текста: {str(e)}")


@router.post("/upload")
async def upload_images(
        files: List[UploadFile] = File(...),
        title: str = Form(...),
        num_questions: int = Form(5)
):
    results = []
    combined_text = ""

    for file in files:
        if not file.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail=f"Файл {file.filename} не является изображением")

        filepath = await save_image(file)

        try:
            text = extract_text_from_image(filepath)
            if text.strip():
                combined_text += text + "\n\n"
                results.append({
                    "filename": file.filename,
                    "text": text
                })
            else:
                results.append({
                    "filename": file.filename,
                    "error": "Не удалось извлечь текст из изображения"
                })

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    if not combined_text.strip():
        raise HTTPException(status_code=400, detail="Не удалось извлечь текст ни из одного изображения")

    # Генерируем тест с указанным количеством вопросов
    questions = generate_questions_from_text(combined_text, num_questions)

    return {
        "test": {
            "title": title,
            "questions": questions,
            "extracted_text": combined_text  # Добавляем извлеченный текст для отладки
        }
    }