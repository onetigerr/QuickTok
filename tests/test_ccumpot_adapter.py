import pytest
from unittest.mock import Mock
from telethon.tl.types import Message, MessageMediaPhoto, MessageMediaDocument, Document
from src.telegram.adapters.ccumpot import CCumpotAdapter
from src.telegram.models import ContentFormat

@pytest.fixture
def adapter():
    return CCumpotAdapter()

def test_extract_metadata_full(adapter):
    text = "Контент модели🦄\n💕ModelName💕\nSetDescription🔥"
    message = Mock(spec=Message)
    message.text = text
    message.message = text
    message.media = Mock(spec=MessageMediaPhoto)
    
    metadata = adapter.extract_metadata(message)
    
    assert metadata.model_name == "ModelName"
    assert metadata.set_name == "SetDescription"
    assert metadata.content_format == ContentFormat.PHOTO

def test_extract_metadata_no_set_name(adapter):
    text = "Контент модели🦄\n💕ModelName💕"
    message = Mock(spec=Message)
    message.text = text
    message.message = text
    message.media = Mock(spec=MessageMediaPhoto)
    
    metadata = adapter.extract_metadata(message)
    
    assert metadata.model_name == "ModelName"
    assert metadata.set_name is None

def test_extract_metadata_unknown_model(adapter):
    text = "Just some random text"
    message = Mock(spec=Message)
    message.text = text
    message.message = text
    message.media = Mock(spec=MessageMediaPhoto)
    
    metadata = adapter.extract_metadata(message)
    
    assert metadata.model_name == "Unknown"

def test_filter_media(adapter):
    message_with_media = Mock(spec=Message)
    message_with_media.media = Mock(spec=MessageMediaPhoto)
    
    message_no_media = Mock(spec=Message)
    message_no_media.media = None
    
    assert adapter.filter(message_with_media) is True
    assert adapter.filter(message_no_media) is False

def test_emoji_stripping(adapter):
    assert adapter._strip_emoji("Hello 🦄 World") == "Hello  World"
    assert adapter._strip_emoji("💕Name💕") == "Name"
