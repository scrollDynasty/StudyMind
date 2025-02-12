from pydantic import BaseModel
from functools import lru_cache

class Settings(BaseModel):
    DATABASE_URL: str = "sqlite:///./studymind.db"
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings()