"""Tests for ASS generator."""

import pytest
from pathlib import Path
import tempfile

from src.subtitles.ass_generator import ASSGenerator
from src.subtitles.models import SubtitleEvent, SubtitleStyle, WordBoundary


def test_generate_basic():
    """Test basic ASS generation."""
    generator = ASSGenerator()

    words = [
        WordBoundary(text="Hello", audio_offset_ms=0, duration_ms=300),
        WordBoundary(text="world", audio_offset_ms=300, duration_ms=400),
    ]

    event = SubtitleEvent(start_time_ms=0, end_time_ms=700, words=words)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.ass"
        result = generator.generate([event], output_path)

        assert result.exists()

        # Read and verify content
        content = result.read_text(encoding="utf-8")

        assert "[Script Info]" in content
        assert "[V4+ Styles]" in content
        assert "[Events]" in content
        assert "Dialogue:" in content


def test_format_timestamp():
    """Test timestamp formatting."""
    generator = ASSGenerator()

    # Test various timestamps
    assert generator._format_timestamp(0) == "0:00:00.00"
    assert generator._format_timestamp(1000) == "0:00:01.00"
    assert generator._format_timestamp(60000) == "0:01:00.00"
    assert generator._format_timestamp(3661500) == "1:01:01.50"


def test_karaoke_tags():
    """Test karaoke tag generation."""
    generator = ASSGenerator()

    words = [
        WordBoundary(text="Hello", audio_offset_ms=0, duration_ms=500),
        WordBoundary(text=",", audio_offset_ms=500, duration_ms=100),
        WordBoundary(text="world", audio_offset_ms=600, duration_ms=400),
    ]

    event = SubtitleEvent(start_time_ms=0, end_time_ms=1000, words=words)

    karaoke_text = generator._generate_karaoke_tags(event)

    # Should have kf tags
    assert "\\kf" in karaoke_text

    # Punctuation should have kf0
    assert "\\kf0" in karaoke_text


def test_custom_style():
    """Test custom style application."""
    style = SubtitleStyle(
        font_name="Helvetica",
        font_size=52,
        primary_color="&H00FF0000",
    )

    generator = ASSGenerator(style)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.ass"

        words = [WordBoundary(text="Test", audio_offset_ms=0, duration_ms=500)]
        event = SubtitleEvent(start_time_ms=0, end_time_ms=500, words=words)

        result = generator.generate([event], output_path)
        content = result.read_text(encoding="utf-8")

        assert "Helvetica" in content
        assert "52" in content
        # Verify Highlight style has BorderStyle 1
        assert "Style: Highlight" in content
        assert "1,3.0,0.0" in content
        # Verify drawing and be tags are present
        assert "\\p1" in content
        assert "\\be" in content


def test_multiple_events():
    """Test generation with multiple events."""
    generator = ASSGenerator()

    events = [
        SubtitleEvent(
            start_time_ms=0,
            end_time_ms=1000,
            words=[WordBoundary(text="First", audio_offset_ms=0, duration_ms=1000)],
        ),
        SubtitleEvent(
            start_time_ms=1000,
            end_time_ms=2000,
            words=[WordBoundary(text="Second", audio_offset_ms=1000, duration_ms=1000)],
        ),
    ]

    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test.ass"
        result = generator.generate(events, output_path)

        content = result.read_text(encoding="utf-8")

        # Layered highlight: 1 background line + (1 box + 1 text) per word per event
        # Event 1: 1 background + 2 lines (1 word) = 3 lines
        # Event 2: 1 background + 2 lines (1 word) = 3 lines
        # Total = 6 lines
        dialogue_count = content.count("Dialogue:")
        assert dialogue_count == 6
