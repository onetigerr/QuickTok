"""Karaoke Subtitles Module

Generates TikTok-ready videos with synchronized TTS audio and karaoke-style subtitles.
"""

from .models import (
    WordBoundary,
    SubtitleEvent,
    TTSResult,
    KaraokeResult,
    KaraokeConfig,
)
from .pipeline import KaraokePipeline

__all__ = [
    "WordBoundary",
    "SubtitleEvent",
    "TTSResult",
    "KaraokeResult",
    "KaraokeConfig",
    "KaraokePipeline",
]
