import sqlite3
from pathlib import Path
from datetime import datetime
from .models import ImportedPost, ContentFormat

class TelegramImportDB:
    def __init__(self, db_path: Path):
        """Инициализация SQLite, создание таблицы если не существует."""
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
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

    def post_exists(self, channel_name: str, post_id: int) -> bool:
        """Проверка дубликата по channel_name + post_id."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM imported_posts WHERE channel_name = ? AND post_id = ?",
                (channel_name, post_id)
            )
            return cursor.fetchone() is not None
    
    def save_post(self, post: ImportedPost) -> int:
        """Сохранение поста, возвращает id."""
        with sqlite3.connect(self.db_path) as conn:
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
        """Получение всех постов канала (для отладки)."""
        with sqlite3.connect(self.db_path) as conn:
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
                    date=datetime.fromisoformat(row['date']) if isinstance(row['date'], str) else row['date'],
                    model_name=row['model_name'],
                    set_name=row['set_name'],
                    content_format=ContentFormat(row['content_format']),
                    file_path=row['file_path']
                ) for row in rows
            ]
    def get_model_by_path(self, file_path_suffix: str) -> str | None:
        """Find model name by matching file path suffix (e.g. Channel/Date)."""
        with sqlite3.connect(self.db_path) as conn:
            # We match strict equality first for safety
            cursor = conn.execute(
                "SELECT model_name FROM imported_posts WHERE file_path = ?",
                (file_path_suffix,)
            )
            row = cursor.fetchone()
            if row:
                return row[0]
            return None
