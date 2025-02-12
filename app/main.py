from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
from pathlib import Path
import os

from app.routers import auth, notes, tests, image_processor

app = FastAPI(title="StudyMind AI")

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
STATIC_DIR = BASE_DIR / "frontend"

# Проверяем наличие папки frontend
if not STATIC_DIR.exists():
    raise Exception(f"Directory {STATIC_DIR} does not exist!")

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(tests.router)
app.include_router(image_processor.router)

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Корневой маршрут - возвращает index.html"""
    try:
        index_path = STATIC_DIR / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {index_path}")

        with open(index_path) as f:
            content = f.read()
            return HTMLResponse(content=content)
    except Exception as e:
        print(f"Error serving index.html: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.exception_handler(404)
async def custom_404_handler(request, exc):
    """Обработчик 404 ошибок"""
    try:
        index_path = STATIC_DIR / "index.html"
        if not index_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {index_path}")

        with open(index_path) as f:
            content = f.read()
            return HTMLResponse(content=content)
    except Exception as e:
        print(f"Error in 404 handler: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Добавляем отладочную информацию при запуске
@app.on_event("startup")
async def startup_event():
    print(f"Starting up with BASE_DIR: {BASE_DIR}")
    print(f"Static files directory: {STATIC_DIR}")
    print(f"Index file exists: {(STATIC_DIR / 'index.html').exists()}")