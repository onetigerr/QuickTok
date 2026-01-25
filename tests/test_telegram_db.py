import pytest
from pathlib import Path
from datetime import datetime
from src.telegram.database import TelegramImportDB
from src.telegram.models import ImportedPost, ContentFormat

@pytest.fixture
def db(tmp_path):
    db_path = tmp_path / "test_telegram.db"
    return TelegramImportDB(db_path)

def test_save_and_retrieve_post(db):
    post = ImportedPost(
        channel_name="test_channel",
        post_id=123,
        date=datetime.now(),
        model_name="Test Model",
        set_name="Test Set",
        content_format=ContentFormat.PHOTO,
        file_path="test_channel/123"
    )
    
    post_id = db.save_post(post)
    assert post_id is not None
    
    fetched_posts = db.get_posts_by_channel("test_channel")
    assert len(fetched_posts) == 1
    fetched = fetched_posts[0]
    
    assert fetched.channel_name == post.channel_name
    assert fetched.post_id == post.post_id
    assert fetched.model_name == post.model_name
    assert fetched.content_format == post.content_format

def test_post_exists(db):
    post = ImportedPost(
        channel_name="test_channel",
        post_id=456,
        date=datetime.now(),
        model_name="Test Model",
        content_format=ContentFormat.VIDEO,
        file_path="test_channel/456"
    )
    db.save_post(post)
    
    assert db.post_exists("test_channel", 456)
    assert not db.post_exists("test_channel", 999)
    assert not db.post_exists("other_channel", 456)

def test_unique_constraint(db):
    post = ImportedPost(
        channel_name="test_channel",
        post_id=789,
        date=datetime.now(),
        model_name="Test Model",
        content_format=ContentFormat.MIXED,
        file_path="test_channel/789"
    )
    db.save_post(post)
    
    # Try to save the same post again
    with pytest.raises(Exception): # SQLite should raise IntegrityError
        db.save_post(post)
