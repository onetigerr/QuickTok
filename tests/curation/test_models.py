import pytest
from src.curation.models import ImageScore
from pydantic import ValidationError

def test_image_score_with_watermark():
    """Test ImageScore model with watermark data."""
    score = ImageScore(
        wow_factor=8,
        engagement=7,
        tiktok_fit=9,
        is_explicit=False,
        reasoning="Good lighting",
        watermark_offset_pct=85.5
    )
    assert score.watermark_offset_pct == 85.5

def test_image_score_without_watermark():
    """Test ImageScore model without watermark (null)."""
    score = ImageScore(
        wow_factor=5,
        engagement=5,
        tiktok_fit=5,
        is_explicit=False,
        reasoning="Average",
        watermark_offset_pct=None
    )
    assert score.watermark_offset_pct is None

def test_image_score_validation():
    """Test watermark offset validation range."""
    # Valid range (0-100)
    ImageScore(wow_factor=1, engagement=1, tiktok_fit=1, is_explicit=False, reasoning="x", watermark_offset_pct=0.0)
    ImageScore(wow_factor=1, engagement=1, tiktok_fit=1, is_explicit=False, reasoning="x", watermark_offset_pct=100.0)
    
    # Invalid range (>100)
    with pytest.raises(ValidationError):
        ImageScore(wow_factor=1, engagement=1, tiktok_fit=1, is_explicit=False, reasoning="x", watermark_offset_pct=100.1)
    
    # Invalid range (<0)
    with pytest.raises(ValidationError):
        ImageScore(wow_factor=1, engagement=1, tiktok_fit=1, is_explicit=False, reasoning="x", watermark_offset_pct=-1.0)
