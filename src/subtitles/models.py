"""Data models for karaoke subtitles module."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class WordBoundary:
    """Represents timing information for a single word from TTS."""

    text: str
    audio_offset_ms: int  # Start time in milliseconds
    duration_ms: int  # Duration in milliseconds


@dataclass
class SubtitleEvent:
    """Represents a single subtitle line with multiple words."""

    start_time_ms: int
    end_time_ms: int
    words: List[WordBoundary]


@dataclass
class TTSResult:
    """Result from TTS synthesis."""

    audio_path: Path
    word_boundaries: List[WordBoundary]
    total_duration_ms: int


@dataclass
class KaraokeResult:
    """Result from karaoke video generation."""

    success: bool
    output_path: Optional[Path]
    artifact_dir: Path
    audio_duration_ms: int
    word_count: int
    segment_count: int
    interpolated_words_pct: float
    error: Optional[str] = None


@dataclass
class NormalizationConfig:
    """Configuration for text normalization."""

    collapse_whitespace: bool = True
    normalize_quotes: bool = True  # Convert fancy quotes to standard
    normalize_dashes: bool = True  # Convert em/en dashes to hyphen
    strip_control_chars: bool = True  # Remove non-printable chars


@dataclass
class SegmentationConfig:
    """Configuration for subtitle segmentation."""

    max_chars_per_line: int = 20  # Maximum characters per subtitle line
    min_words_per_segment: int = 1  # Minimum words before line break
    max_words_per_segment: int = 3  # Maximum words per segment


@dataclass
class SubtitleStyle:
    """Visual style configuration for ASS subtitles."""

    font_name: str = "Arial Bold"
    font_size: int = 100
    primary_color: str = "&H00FFFFFF"  # White (text color)
    secondary_color: str = "&H005500FF"  # Pink (active highlight color)
    highlight_color: str = "&H005500FF"  # Pink box fill
    inactive_color: str = "&H00FFFFFF"  # White (text color for background layer)
    outline_width: float = 3.0  # Black border thickness for letters
    box_blur: float = 8.0  # Softness of the box edges
    box_radius: float = 20.0  # Corner radius for the box
    outline_color: str = "&H00000000"  # Black outline
    back_color: str = "&H00000000"  # Black back color (used for shadow)
    shadow_depth: float = 0.0
    alignment: int = 2  # Bottom center
    margin_v: int = 300  # Vertical margin from bottom
    margin_l: int = 60
    margin_r: int = 60
    use_box_highlight: bool = True  # Enable layered highlight box
    use_uppercase: bool = True  # All text must be UPPERCASE


@dataclass
class RendererConfig:
    """Configuration for video rendering."""

    target_width: int = 1080
    target_height: int = 1920
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = 23  # Quality (lower = better)
    preset: str = "medium"


@dataclass
class KaraokeConfig:
    """Main configuration for karaoke pipeline."""

    language: str = "es-ES"
    voice: str = "es-ES-ElviraNeural"
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    segmentation: SegmentationConfig = field(default_factory=SegmentationConfig)
    style: SubtitleStyle = field(default_factory=SubtitleStyle)
    renderer: RendererConfig = field(default_factory=RendererConfig)
