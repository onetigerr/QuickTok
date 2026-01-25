import re
from telethon.tl.types import Message
from ..models import NormalizedMetadata, ContentFormat
from .base import BaseAdapter

# Regex для удаления emoji
EMOJI_PATTERN = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # flags
    "\U0001F900-\U0001F9FF"  # supplemental symbols
    "\u2702-\u27b0"
    "\u24c2-\U0001F251"
    "]+",
    flags=re.UNICODE
)

class CCumpotAdapter(BaseAdapter):
    @property
    def channel_name(self) -> str:
        return "CCumpot"
    
    def filter(self, message: Message) -> bool:
        # Фильтрация отключена — принимаем все посты с медиа
        return message.media is not None
    
    def extract_metadata(self, message: Message) -> NormalizedMetadata:
        text = message.text or message.message or ""
        model_name = self._parse_model_name(text)
        set_name = self._parse_set_name(text)
        content_format = self._detect_format(message)
        return NormalizedMetadata(
            model_name=model_name,
            set_name=set_name,
            content_format=content_format
        )
    
    def _strip_emoji(self, text: str) -> str:
        """Удаляет все emoji из строки."""
        return EMOJI_PATTERN.sub('', text).strip()
    
    def _parse_model_name(self, text: str) -> str:
        """Извлекает имя модели из второй строки, очищая от emoji."""
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return "Unknown"
        second_line = self._strip_emoji(lines[1])
        return second_line if second_line else "Unknown"
    
    def _parse_set_name(self, text: str) -> str | None:
        """Извлекает название сета из третьей строки, очищая от emoji."""
        lines = text.strip().split('\n')
        if len(lines) < 3:
            return None
        third_line = self._strip_emoji(lines[2])
        return third_line if third_line else None
        
    def _detect_format(self, message: Message) -> ContentFormat:
        if not message.media:
             # Fallback, though filter() should prevent this
            return ContentFormat.PHOTO
            
        # Simplistic detection logic - can be refined based on actual telethon types
        # For now we'll assume mixed or infer from attributes if possible.
        # But per design we just need reasonable defaults.
        # Telethon MessageMediaPhoto vs MessageMediaDocument (video/gif)
        
        from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
        
        if isinstance(message.media, MessageMediaPhoto):
            return ContentFormat.PHOTO
        if isinstance(message.media, MessageMediaDocument):
             # Check mime type or attributes for video
             if hasattr(message.media, 'document'):
                 mime = getattr(message.media.document, 'mime_type', '')
                 if 'video' in mime:
                     return ContentFormat.VIDEO
        
        return ContentFormat.MIXED
