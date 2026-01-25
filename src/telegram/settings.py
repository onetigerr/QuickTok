"""
Configuration settings for Telegram import module.
"""
from pathlib import Path

# File size limits
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Directories
SESSIONS_DIR = Path("data/sessions")
INCOMING_DIR = Path("data/incoming")
DATABASE_PATH = Path("data/telegram_imports.db")

# Error handling
MAX_CONSECUTIVE_ERRORS = 3
