import sqlite3
from pathlib import Path
from datetime import datetime
from .models import ImportedPost, ContentFormat

def adapt_datetime(dt: datetime) -> str:
    return dt.isoformat()

def convert_datetime(val: bytes) -> datetime:
    return datetime.fromisoformat(val.decode())

# Register adapters and converters for Python 3.12+ compatibility
sqlite3.register_adapter(datetime, adapt_datetime)
sqlite3.register_converter("TIMESTAMP", convert_datetime)
sqlite3.register_converter("timestamp", convert_datetime)

class TelegramImportDB:
    def __init__(self, db_path: Path):
        """Initialize SQLite, create table if not exists."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS imported_posts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    channel_name TEXT NOT NULL,
                    post_id INTEGER NOT NULL,
                    date TIMESTAMP NOT NULL,
                    model_name TEXT NOT NULL,
                    set_name TEXT,
                    content_format TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(channel_name, post_id)
                );
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS photo_scores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL UNIQUE,
                    wow_factor INTEGER NOT NULL,
                    engagement INTEGER NOT NULL,
                    tiktok_fit INTEGER NOT NULL,
                    combined_score REAL NOT NULL,
                    reasoning TEXT NOT NULL,
                    model_name TEXT,
                    watermark_offset_pct REAL,
                    scored_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)

    def post_exists(self, channel_name: str, post_id: int) -> bool:
        """Check for duplicate by channel_name + post_id."""
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM imported_posts WHERE channel_name = ? AND post_id = ?",
                (channel_name, post_id)
            )
            return cursor.fetchone() is not None
    
    def save_post(self, post: ImportedPost) -> int:
        """Save post record, returns auto-generated id."""
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.execute(
                """
                INSERT INTO imported_posts 
                (channel_name, post_id, date, model_name, set_name, content_format, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    post.channel_name,
                    post.post_id,
                    post.date,
                    post.model_name,
                    post.set_name,
                    post.content_format.value,
                    post.file_path
                )
            )
            if post.id is None:
                post.id = cursor.lastrowid
            return cursor.lastrowid
    
    def get_posts_by_channel(self, channel_name: str) -> list[ImportedPost]:
        """Get all channel posts (for debugging)."""
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM imported_posts WHERE channel_name = ?",
                (channel_name,)
            )
            rows = cursor.fetchall()
            return [
                ImportedPost(
                    id=row['id'],
                    channel_name=row['channel_name'],
                    post_id=row['post_id'],
                    date=row['date'],
                    model_name=row['model_name'],
                    set_name=row['set_name'],
                    content_format=ContentFormat(row['content_format']),
                    file_path=row['file_path']
                ) for row in rows
            ]
    def get_model_by_path(self, file_path_suffix: str) -> str | None:
        """Find model name by matching file path suffix (e.g. Channel/Date)."""
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            # We match strict equality first for safety
            cursor = conn.execute(
                "SELECT model_name FROM imported_posts WHERE file_path = ?",
                (file_path_suffix,)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
            return None

    def mark_post_processed(self, file_path_suffix: str):
        """Mark a post as processed by curation pipeline."""
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            conn.execute(
                "UPDATE imported_posts SET curation_processed = 1 WHERE file_path = ?",
                (file_path_suffix,)
            )

    def is_post_processed(self, file_path_suffix: str) -> bool:
        """Check if post was already marked as processed."""
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            cursor = conn.execute(
                "SELECT curation_processed FROM imported_posts WHERE file_path = ?",
                (file_path_suffix,)
            )
            row = cursor.fetchone()
            if row:
                return bool(row[0])
            return False

    def save_photo_score(self, file_path: str, score: dict, model_name: str = None) -> int | None:
        """
        Save photo score to database. Skips explicit photos.
        Returns the inserted row id or None if skipped/duplicate.
        
        Args:
            file_path: Relative path to the photo file
            score: Dict with keys: wow_factor, engagement, tiktok_fit, is_explicit, reasoning
            model_name: Optional model name from imported_posts
        """
        # Skip explicit photos
        if score.get('is_explicit', False):
            return None
        
        combined = round((score['wow_factor'] + score['engagement'] + score['tiktok_fit']) / 3.0, 1)
        
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO photo_scores 
                    (file_path, wow_factor, engagement, tiktok_fit, combined_score, 
                     reasoning, model_name, watermark_offset_pct)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        file_path,
                        score['wow_factor'],
                        score['engagement'],
                        score['tiktok_fit'],
                        combined,
                        score['reasoning'],
                        model_name,
                        score.get('watermark_offset_pct')
                    )
                )
                return cursor.lastrowid
            except sqlite3.IntegrityError:
                # Duplicate file_path, skip silently
                return None
    
    def get_photo_score(self, file_path: str) -> dict | None:
        """Get photo score by file path."""
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM photo_scores WHERE file_path = ?",
                (file_path,)
            )
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    def get_all_scores(self, min_score: float = None) -> list[dict]:
        """
        Get all photo scores with optional filters.
        
        Args:
            min_score: Optional minimum combined_score filter
        """
        with sqlite3.connect(self.db_path, detect_types=sqlite3.PARSE_DECLTYPES) as conn:
            conn.row_factory = sqlite3.Row
            
            query = "SELECT * FROM photo_scores"
            params = []
            
            if min_score is not None:
                query += " WHERE combined_score >= ?"
                params.append(min_score)
            
            query += " ORDER BY combined_score DESC"
            
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

