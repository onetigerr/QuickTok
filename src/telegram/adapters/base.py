from abc import ABC, abstractmethod
from telethon.tl.types import Message
from ..models import NormalizedMetadata

class BaseAdapter(ABC):
    @property
    @abstractmethod
    def channel_name(self) -> str:
        """Name of the channel this adapter processes."""
        pass
    
    @abstractmethod
    def filter(self, message: Message) -> bool:
        """
        Returns True if the post should be downloaded.
        Used for filtering ads, service posts, etc.
        """
        pass
    
    @abstractmethod
    def extract_metadata(self, message: Message) -> NormalizedMetadata:
        """
        Extracts structured metadata from the message.
        Returns NormalizedMetadata with model_name, set_name, etc.
        """
        pass
