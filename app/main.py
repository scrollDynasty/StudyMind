from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
import pytesseract
from PIL import Image
import cv2
import numpy as np
import io
import os
import re
from transformers import pipeline

# Создаем новый экземпляр FastAPI
app = FastAPI()

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Определяем базовые пути
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"
UPLOADS_DIR = BASE_DIR / "uploads"

# Создаем папку для загрузок, если её нет
UPLOADS_DIR.mkdir(exist_ok=True)

# Определяем путь к index.html
index_path = FRONTEND_DIR / "index.html"

# Проверяем наличие index.html при запуске
if not index_path.exists():
    raise Exception(f"index.html not found at {index_path}")

print(f"Base directory: {BASE_DIR}")
print(f"Frontend directory: {FRONTEND_DIR}")
print(f"Index.html exists: {index_path.exists()}")
print(f"Index.html absolute path: {index_path.absolute()}")

# Для Windows нужно указать путь к Tesseract
if os.name == 'nt':
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


def enhance_image(image):
    """Улучшенная предобработка изображения специально для русского текста"""
    img_array = np.array(image)

    # Увеличиваем размер изображения для лучшего распознавания
    height, width = img_array.shape[:2]
    img_array = cv2.resize(img_array, (width * 2, height * 2))

    # Конвертируем в оттенки серого
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

    # Увеличиваем контраст
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    contrast = clahe.apply(gray)

    # Адаптивная бинаризация
    binary = cv2.adaptiveThreshold(
        contrast, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2
    )

    # Удаление шума
    denoised = cv2.fastNlMeansDenoising(binary)

    return Image.fromarray(denoised)


def extract_text(image):
    """Улучшенное извлечение русского текста"""
    # Настройки специально для русского языка
    custom_config = r'--oem 3 --psm 6 -l rus --dpi 300'

    # Получаем данные о расположении текста
    data = pytesseract.image_to_data(image, config=custom_config, output_type=pytesseract.Output.DICT)

    # Собираем только уверенно распознанный текст
    confident_text = []
    for i, conf in enumerate(data['conf']):
        if float(conf) > 60:  # берем только текст с уверенностью > 60%
            text = data['text'][i].strip()
            if text:
                confident_text.append(text)

    return ' '.join(confident_text)


def clean_text(text):
    """Улучшенная очистка и нормализация русского текста"""
    # Замена часто неправильно распознаваемых символов
    replacements = {
        'B': 'В',
        '3': 'З',
        '0': 'О',
        '6': 'б',
        '9': 'э',
        'p': 'р',
        'A': 'А',
        'T': 'Т',
        'M': 'М',
        'E': 'Е',
        'H': 'Н',
        'K': 'К',
        'X': 'Х',
        'C': 'С'
    }

    for eng, rus in replacements.items():
        text = text.replace(eng, rus)

    # Удаляем лишние пробелы и специальные символы
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s\.\,\?\!\-]', '', text)

    return text.strip()


def analyze_text_type(text):
    """Определение типа текста на русском языке"""
    patterns = {
        'math': r'\b(уравнение|график|функция|теорема|число|сложение|вычитание|умножение|деление)\b',
        'history': r'\b(век|год|император|царь|война|битва|сражение|династия|государство|правитель)\b',
        'geography': r'\b(река|гора|океан|материк|климат|рельеф|почва|население|страна|город)\b',
        'literature': r'\b(роман|поэма|автор|писатель|произведение|герой|сюжет|персонаж|литература)\b'
    }

    text_type = 'general'
    max_matches = 0

    for type_name, pattern in patterns.items():
        matches = len(re.findall(pattern, text.lower(), re.IGNORECASE))
        if matches > max_matches:
            max_matches = matches
            text_type = type_name

    return text_type


def extract_key_points(text, num_points=5):
    """Извлечение ключевых моментов из текста"""
    # Разбиваем текст на предложения
    sentences = [s.strip() for s in re.split('[.!?]', text) if s.strip()]

    # Если предложений меньше, чем нужно точек, возвращаем все
    if len(sentences) <= num_points:
        return sentences

    # Выбираем предложения с равным интервалом
    step = len(sentences) / num_points
    key_points = []

    for i in range(num_points):
        idx = int(i * step)
        if idx < len(sentences):
            key_points.append(sentences[idx])

    return key_points


def generate_questions(text, subject_type, num_questions=5):
    """Генерация вопросов на русском языке"""
    # Получаем ключевые моменты из текста
    key_points = extract_key_points(text, num_questions)

    if not key_points:
        return []

    # Шаблоны вопросов для разных предметов
    subject_patterns = {
        'history': [
            "Какое историческое событие описывается в отрывке: {}?",
            "В каком году произошло событие: {}?",
            "Кто был правителем в период: {}?",
            "Какие исторические последствия имели события: {}?",
            "Какая историческая эпоха описывается в тексте: {}?"
        ],
        'geography': [
            "Какой географический объект описывается в отрывке: {}?",
            "Где находится: {}?",
            "Какие природные особенности характерны для: {}?",
            "Какой климат характерен для территории: {}?",
            "Какие природные ресурсы встречаются в: {}?"
        ],
        'math': [
            "Как решается задача: {}?",
            "Какой метод используется для решения: {}?",
            "Что является ответом в примере: {}?",
            "Какая формула применяется в случае: {}?",
            "Какие математические операции нужно выполнить: {}?"
        ],
        'literature': [
            "Кто автор произведения: {}?",
            "Какой литературный жанр представлен в отрывке: {}?",
            "Кто главный герой в отрывке: {}?",
            "Какая основная мысль отрывка: {}?",
            "Какие художественные приемы использованы в тексте: {}?"
        ],
        'general': [
            "О чем говорится в отрывке: {}?",
            "Какая основная мысль текста: {}?",
            "Что является главным в отрывке: {}?",
            "Какой вывод можно сделать из отрывка: {}?",
            "Какая информация представлена в тексте: {}?"
        ]
    }

    patterns = subject_patterns.get(subject_type, subject_patterns['general'])
    questions = []

    for i, point in enumerate(key_points):
        if i >= num_questions:
            break

        pattern = patterns[i % len(patterns)]
        question_text = pattern.format(point)

        # Генерируем варианты ответов
        correct_answer = point
        wrong_answers = [
            f"Это не отражает содержание отрывка: {point[:len(point) // 2]}...",
            "Информация отсутствует в тексте",
            "В тексте об этом не упоминается"
        ]

        questions.append({
            "id": i + 1,
            "text": question_text,
            "options": [correct_answer] + wrong_answers,
            "correct_answer": correct_answer
        })

    return questions


@app.post("/api/images/upload")
async def upload_image(
        file: UploadFile = File(...),
        title: str = None,
        num_questions: int = 5
):
    try:
        # Читаем и обрабатываем изображение
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        enhanced_image = enhance_image(image)

        # Извлекаем и очищаем текст
        raw_text = extract_text(enhanced_image)
        cleaned_text = clean_text(raw_text)

        if not cleaned_text.strip():
            raise HTTPException(status_code=400, detail="Не удалось распознать текст на изображении")

        # Определяем тип текста и генерируем вопросы
        subject_type = analyze_text_type(cleaned_text)
        questions = generate_questions(cleaned_text, subject_type, num_questions)

        # Словарь для перевода типа предмета
        subject_names = {
            'math': 'математике',
            'history': 'истории',
            'geography': 'географии',
            'literature': 'литературе',
            'general': 'общим знаниям'
        }

        return {
            "test": {
                "title": title or f"Тест по {subject_names.get(subject_type, 'предмету')}",
                "questions": questions,
                "subject_type": subject_type,
                "original_text": cleaned_text
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка обработки изображения: {str(e)}"
        )


@app.post("/api/tests/generate")
async def generate_test(
        title: str = None,
        content: str = None,
        num_questions: int = 5
):
    try:
        if not content:
            raise HTTPException(status_code=400, detail="Текст для генерации теста не предоставлен")

        subject_type = analyze_text_type(content)
        questions = generate_questions(content, subject_type, num_questions)

        subject_names = {
            'math': 'математике',
            'history': 'истории',
            'geography': 'географии',
            'literature': 'литературе',
            'general': 'общим знаниям'
        }

        return {
            "test": {
                "title": title or f"Тест по {subject_names.get(subject_type, 'предмету')}",
                "questions": questions,
                "subject_type": subject_type
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка генерации теста: {str(e)}"
        )


@app.get("/")
async def root():
    """Корневой маршрут - отдает index.html"""
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="index.html not found")
    return FileResponse(index_path)


# Монтируем статические файлы
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)