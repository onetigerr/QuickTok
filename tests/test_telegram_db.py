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


# ====================
# Photo Scores Tests
# ====================

def test_photo_scores_table_creation(db):
    """Test that photo_scores table is created with correct schema."""
    import sqlite3
    conn = sqlite3.connect(db.db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='photo_scores'")
    result = cursor.fetchone()
    conn.close()
    
    assert result is not None, "photo_scores table should be created"


def test_save_and_get_photo_score(db):
    """Test saving and retrieving a photo score."""
    score_dict = {
        'wow_factor': 8,
        'engagement': 9,
        'tiktok_fit': 7,
        'is_explicit': False,
        'reasoning': 'Great image with good composition'
    }
    
    row_id = db.save_photo_score('test/image1.jpg', score_dict, 'Test Model')
    assert row_id is not None
    
    # Retrieve the score
    retrieved = db.get_photo_score('test/image1.jpg')
    assert retrieved is not None
    assert retrieved['wow_factor'] == 8
    assert retrieved['engagement'] == 9
    assert retrieved['tiktok_fit'] == 7
    assert retrieved['reasoning'] == 'Great image with good composition'
    assert retrieved['model_name'] == 'Test Model'
    assert abs(retrieved['combined_score'] - 8.0) < 0.01


def test_photo_score_unique_constraint(db):
    """Test that duplicate file_path cannot be inserted."""
    score_dict = {
        'wow_factor': 8,
        'engagement': 9,
        'tiktok_fit': 7,
        'is_explicit': False,
        'reasoning': 'First attempt'
    }
    
    # First save should succeed
    row_id1 = db.save_photo_score('test/duplicate.jpg', score_dict)
    assert row_id1 is not None
    
    # Second save with same file_path should return None (silently skip)
    score_dict['reasoning'] = 'Second attempt'
    row_id2 = db.save_photo_score('test/duplicate.jpg', score_dict)
    assert row_id2 is None
    
    # Verify only one record exists
    retrieved = db.get_photo_score('test/duplicate.jpg')
    assert retrieved['reasoning'] == 'First attempt'  # Original should remain


def test_explicit_photos_not_saved(db):
    """Test that explicit photos are not saved to the database."""
    explicit_score = {
        'wow_factor': 10,
        'engagement': 10,
        'tiktok_fit': 10,
        'is_explicit': True,
        'reasoning': 'Explicit content detected'
    }
    
    row_id = db.save_photo_score('test/explicit.jpg', explicit_score)
    assert row_id is None, "Explicit photos should not be saved"
    
    # Verify it's not in the database
    retrieved = db.get_photo_score('test/explicit.jpg')
    assert retrieved is None


def test_get_all_scores(db):
    """Test retrieving all scores with filters."""
    # Add multiple scores
    scores = [
        ('test/photo1.jpg', {'wow_factor': 9, 'engagement': 8, 'tiktok_fit': 9, 'is_explicit': False, 'reasoning': 'Good'}),
        ('test/photo2.jpg', {'wow_factor': 5, 'engagement': 6, 'tiktok_fit': 5, 'is_explicit': False, 'reasoning': 'Average'}),
        ('test/photo3.jpg', {'wow_factor': 10, 'engagement': 10, 'tiktok_fit': 10, 'is_explicit': False, 'reasoning': 'Excellent'}),
    ]
    
    for path, score in scores:
        db.save_photo_score(path, score)
    
    # Get all scores
    all_scores = db.get_all_scores()
    assert len(all_scores) == 3
    
    # Scores should be ordered by combined_score descending
    assert all_scores[0]['file_path'] == 'test/photo3.jpg'
    assert all_scores[1]['file_path'] == 'test/photo1.jpg'
    assert all_scores[2]['file_path'] == 'test/photo2.jpg'
    
    # Filter by minimum score
    high_scores = db.get_all_scores(min_score=8.0)
    assert len(high_scores) == 2
    assert 'photo3.jpg' in high_scores[0]['file_path']
    assert 'photo1.jpg' in high_scores[1]['file_path']


def test_save_photo_score_without_model_name(db):
    """Test saving a score without model_name (should still work)."""
    score_dict = {
        'wow_factor': 7,
        'engagement': 7,
        'tiktok_fit': 7,
        'is_explicit': False,
        'reasoning': 'No model name'
    }
    
    row_id = db.save_photo_score('test/no_model.jpg', score_dict)
    assert row_id is not None
    
    retrieved = db.get_photo_score('test/no_model.jpg')
    assert retrieved['model_name'] is None

def test_save_photo_score_with_watermark(db):
    """Test saving and retrieving a photo score with watermark data."""
    score_dict = {
        'wow_factor': 8,
        'engagement': 9,
        'tiktok_fit': 7,
        'is_explicit': False,
        'reasoning': 'Watermark at bottom',
        'watermark_offset_pct': 92.5
    }
    
    db.save_photo_score('test/watermark.jpg', score_dict)
    retrieved = db.get_photo_score('test/watermark.jpg')
    
    assert retrieved['watermark_offset_pct'] == 92.5

def test_save_photo_score_without_watermark(db):
    """Test saving and retrieving a photo score without watermark data."""
    score_dict = {
        'wow_factor': 5,
        'engagement': 5,
        'tiktok_fit': 5,
        'is_explicit': False,
        'reasoning': 'Clean image',
        'watermark_offset_pct': None
    }
    
    db.save_photo_score('test/clean.jpg', score_dict)
    retrieved = db.get_photo_score('test/clean.jpg')
    
    # In SQLite, None is NULL
    assert retrieved['watermark_offset_pct'] is None
