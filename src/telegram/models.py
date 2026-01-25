from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class ContentFormat(str, Enum):
    PHOTO = "photo"
    VIDEO = "video"
    MIXED = "mixed"

class NormalizedMetadata(BaseModel):
    """Выход адаптера — нормализованные метаданные."""
    model_name: str
    set_name: str | None = None
    content_format: ContentFormat

class ImportedPost(BaseModel):
    """Запись в БД об импортированном посте."""
    id: int | None = None  # SQLite autoincrement
    channel_name: str
    post_id: int  # ID сообщения в канале
    date: datetime
    model_name: str
    set_name: str | None = None
    content_format: ContentFormat
    file_path: str  # Относительный путь к папке с контентом

class ImportResult(BaseModel):
    """Результат импорта."""
    total_processed: int
    downloaded: int
    skipped_duplicates: int
    errors: int
    stopped_early: bool = False  # True если прервано из-за 3 ошибок
