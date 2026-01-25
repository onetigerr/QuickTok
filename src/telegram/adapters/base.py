from abc import ABC, abstractmethod
from telethon.tl.types import Message
from ..models import NormalizedMetadata

class BaseAdapter(ABC):
    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Имя канала, который обрабатывает этот адаптер."""
        pass
    
    @abstractmethod
    def filter(self, message: Message) -> bool:
        """
        Возвращает True, если пост нужно скачивать.
        Используется для фильтрации рекламы, служебных постов и т.д.
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, message: Message) -> NormalizedMetadata:
        """
        Извлекает структурированные метаданные из сообщения.
        Возвращает NormalizedMetadata с model_name, set_name и т.д.
        """
        pass
