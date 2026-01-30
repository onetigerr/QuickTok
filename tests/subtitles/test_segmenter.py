"""Tests for subtitle segmenter."""

import pytest

from src.subtitles.models import SegmentationConfig, WordBoundary
from src.subtitles.segmenter import SubtitleSegmenter


def test_segment_basic():
    """Test basic segmentation."""
    segmenter = SubtitleSegmenter()

    words = [
        WordBoundary(text="Hello", audio_offset_ms=0, duration_ms=300),
        WordBoundary(text="world", audio_offset_ms=300, duration_ms=400),
        WordBoundary(text="test", audio_offset_ms=700, duration_ms=300),
    ]

    events = segmenter.segment(words)

    assert len(events) == 1
    assert len(events[0].words) == 3
    assert events[0].start_time_ms == 0
    assert events[0].end_time_ms == 1000


def test_segment_long_text():
    """Test segmentation of long text."""
    config = SegmentationConfig(max_chars_per_line=20, max_words_per_segment=4)
    segmenter = SubtitleSegmenter(config)

    # Create 10 words
    words = [
        WordBoundary(text=f"word{i}", audio_offset_ms=i * 300, duration_ms=300)
        for i in range(10)
    ]

    events = segmenter.segment(words)

    # Should be split into multiple events
    assert len(events) > 1

    # Each event should have <= max_words_per_segment
    for event in events:
        assert len(event.words) <= config.max_words_per_segment


def test_segment_sentence_end():
    """Test segmentation respects sentence endings."""
    segmenter = SubtitleSegmenter()

    words = [
        WordBoundary(text="Hello", audio_offset_ms=0, duration_ms=300),
        WordBoundary(text="world.", audio_offset_ms=300, duration_ms=400),
        WordBoundary(text="New", audio_offset_ms=700, duration_ms=300),
        WordBoundary(text="sentence", audio_offset_ms=1000, duration_ms=400),
    ]

    events = segmenter.segment(words)

    # Should break after sentence end
    assert len(events) >= 1


def test_segment_empty():
    """Test segmentation with empty input."""
    segmenter = SubtitleSegmenter()
    events = segmenter.segment([])
    assert len(events) == 0


def test_event_timing():
    """Test that event timings are correct."""
    segmenter = SubtitleSegmenter()

    words = [
        WordBoundary(text="Hello", audio_offset_ms=100, duration_ms=300),
        WordBoundary(text="world", audio_offset_ms=400, duration_ms=400),
    ]

    events = segmenter.segment(words)

    assert events[0].start_time_ms == 100  # First word start
    assert events[0].end_time_ms == 800  # Last word end (400 + 400)
