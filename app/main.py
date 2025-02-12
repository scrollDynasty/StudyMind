from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path

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

# Проверяем наличие index.html при запуске
index_path = FRONTEND_DIR / "index.html"
if not index_path.exists():
    raise Exception(f"index.html not found at {index_path}")

print(f"Base directory: {BASE_DIR}")
print(f"Frontend directory: {FRONTEND_DIR}")
print(f"Index.html exists: {index_path.exists()}")
print(f"Index.html absolute path: {index_path.absolute()}")

# Определяем корневой маршрут ДО монтирования статических файлов
@app.get("/")
async def root():
    """Корневой маршрут - отдает index.html"""
    return FileResponse(index_path)

# Монтируем статические файлы ПОСЛЕ определения корневого маршрута
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

# Тестовый API эндпоинт
@app.post("/api/tests/generate")
async def generate_test():
    return {
        "test": {
            "title": "Тестовый тест",
            "questions": [
                {
                    "id": 1,
                    "text": "Пример вопроса",
                    "options": ["A", "B", "C", "D"],
                    "correct_answer": "A"
                }
            ]
        }
    }

# Тестовый эндпоинт для проверки
@app.get("/test")
async def test():
    return {"status": "API working"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)