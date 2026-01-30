from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class ContentFormat(str, Enum):
    PHOTO = "photo"
    VIDEO = "video"
    MIXED = "mixed"

class NormalizedMetadata(BaseModel):
    """Adapter output — normalized metadata."""
    model_name: str
    set_name: str | None = None
    content_format: ContentFormat

class ImportedPost(BaseModel):
    """Database record for an imported post."""
    id: int | None = None  # SQLite autoincrement
    channel_name: str
    post_id: int  # Original message ID in the channel
    date: datetime
    model_name: str
    set_name: str | None = None
    content_format: ContentFormat
    file_path: str  # Relative path to the folder with content

class ImportResult(BaseModel):
    """Result of the import process."""
    total_processed: int
    downloaded: int
    skipped_duplicates: int
    errors: int
    stopped_early: bool = False  # True if interrupted due to 3 consecutive errors
