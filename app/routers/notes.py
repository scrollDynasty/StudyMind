from fastapi import APIRouter, Depends, HTTPException,UploadFile, File
from pydantic import BaseModel
from typing import List
from app.ml.text_processor import TextProcessor

router = APIRouter(prefix="/notes", tags=["notes"])

class NoteBase(BaseModel):
    title: str
    content: str

class NoteCreate(NoteBase):
    pass

class Note(NoteBase):
    id: int
    user_id: int

    class Config:
        orm_mode = True

@router.post("/", response_model=Note)
async def create_note(note: NoteCreate):
    # Здесь должна быть логика создания заметки
    return {"id": 1, "title": note.title, "content": note.content, "user_id": 1}

@router.get("/", response_model=List[Note])
async def read_notes():
    # Здесь должна быть логика получения заметок
    return []

@router.get("/{note_id}", response_model=Note)
async def read_note(note_id: int):
    # Здесь должна быть логика получения конкретной заметки
    return {"id": note_id, "title": "Test Note", "content": "Test Content", "user_id": 1}


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = content.decode()

        # Обработка текста с помощью нашего процессора
        processor = TextProcessor()
        key_concepts = processor.extract_key_concepts(text)

        return {
            "status": "success",
            "filename": file.filename,
            "key_concepts": key_concepts,
            "content_preview": text[:200] + "..."  # Превью содержимого
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }