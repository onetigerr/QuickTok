import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from src.curation.scorer import ImageScorer
from src.curation.models import ImageScore

@pytest.fixture
def mock_llm_response():
    return {
        "wow_factor": 8,
        "engagement": 7,
        "tiktok_fit": 9,
        "is_explicit": False,
        "reasoning": "Great lighting and pose."
    }

@pytest.fixture
def mock_batch_response():
    return {
        "scores": [
            {
                "wow_factor": 8,
                "engagement": 8,
                "tiktok_fit": 8,
                "is_explicit": False,
                "reasoning": "Img 1 good"
            },
            {
                "wow_factor": 2,
                "engagement": 2,
                "tiktok_fit": 2,
                "is_explicit": False,
                "reasoning": "Img 2 bad"
            }
        ]
    }

@pytest.fixture
def scorer():
    with patch("src.curation.scorer.ChatGroq") as MockGroq:
        # Mock instance
        mock_instance = MockGroq.return_value
        scorer = ImageScorer(api_key="fake_key")
        scorer.llm = mock_instance
        yield scorer

@pytest.mark.asyncio
async def test_score_single(scorer, mock_llm_response, tmp_path):
    # Setup mock
    # content attribute of response
    mock_msg = MagicMock()
    mock_msg.content = mock_llm_response
    scorer.llm.ainvoke = AsyncMock(return_value=mock_msg)
    
    # Mock thumbnail gen
    dummy_path = tmp_path / "test.jpg"
    dummy_path.touch()
    
    with patch("src.curation.scorer.ThumbnailGenerator.to_base64", return_value="base64str"):
        # Mock Parser behavior since we are mocking ainvoke return to be a dict directly or string?
        # Real llm returns a message with .content as string.
        # But we can also mock the parser.
        # Let's mock ainvoke to return a string JSON
        import json
        mock_msg.content = json.dumps(mock_llm_response)
        
        result = await scorer.score(dummy_path)
        
        assert isinstance(result, ImageScore)
        assert result.wow_factor == 8
        assert result.combined_score == 8.0
        assert not result.is_explicit

@pytest.mark.asyncio
async def test_score_explicit(scorer, tmp_path):
    explicit_resp = {
        "wow_factor": 0, "engagement": 0, "tiktok_fit": 0,
        "is_explicit": True, "reasoning": "NSFW"
    }
    
    mock_msg = MagicMock()
    import json
    mock_msg.content = json.dumps(explicit_resp)
    scorer.llm.ainvoke = AsyncMock(return_value=mock_msg)
    
    dummy_path = tmp_path / "explicit.jpg"
    dummy_path.touch()
    
    with patch("src.curation.scorer.ThumbnailGenerator.to_base64", return_value="base64str"):
        result = await scorer.score(dummy_path)
        assert result.is_explicit
        assert result.combined_score == 0.0

@pytest.mark.asyncio
async def test_score_batch_success(scorer, mock_batch_response, tmp_path):
    mock_msg = MagicMock()
    import json
    mock_msg.content = json.dumps(mock_batch_response)
    scorer.llm.ainvoke = AsyncMock(return_value=mock_msg)
    
    paths = [tmp_path / "1.jpg", tmp_path / "2.jpg"]
    for p in paths: p.touch()
    
    with patch("src.curation.scorer.ThumbnailGenerator.to_base64", return_value="base64str"):
        results = await scorer.score_batch(paths)
        
        assert len(results) == 2
        assert results[0].wow_factor == 8
        assert results[1].wow_factor == 2

@pytest.mark.asyncio
async def test_score_batch_mismatch(scorer, mock_batch_response, tmp_path):
    """Test when API returns fewer/more scores than images."""
    mock_msg = MagicMock()
    import json
    mock_msg.content = json.dumps(mock_batch_response) # Returns 2 scores
    scorer.llm.ainvoke = AsyncMock(return_value=mock_msg)
    
    # Send 3 paths
    paths = [tmp_path / "1.jpg", tmp_path / "2.jpg", tmp_path / "3.jpg"]
    for p in paths: p.touch()
    
    with patch("src.curation.scorer.ThumbnailGenerator.to_base64", return_value="base64str"):
        with pytest.raises(RuntimeError, match="Batch scoring failed"):
            await scorer.score_batch(paths)
