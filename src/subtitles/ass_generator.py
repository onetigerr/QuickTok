"""ASS subtitle file generation with karaoke effects."""

import re
from pathlib import Path
from typing import List, Tuple

from PIL import ImageFont

from .models import SubtitleEvent, SubtitleStyle


class ASSGenerator:
    """Generates ASS subtitle files with karaoke tags."""

    def __init__(self, style: SubtitleStyle = None):
        """Initialize ASS generator.

        Args:
            style: Subtitle style configuration
        """
        self.style = style or SubtitleStyle()
        self._font = self._load_font()

    def _load_font(self) -> ImageFont.FreeTypeFont:
        """Load font for metrics calculation."""
        # Try common paths on macOS
        font_paths = [
            Path("/System/Library/Fonts/Supplemental/Arial Bold.ttf"),
            Path("/Library/Fonts/Arial Bold.ttf"),
            Path("/System/Library/Fonts/Supplemental/Arial.ttf"),
        ]
        for path in font_paths:
            if path.exists():
                return ImageFont.truetype(str(path), self.style.font_size)
        
        # Fallback to default pillow font if none found (less accurate)
        return ImageFont.load_default()

    def _get_text_width(self, text: str) -> float:
        """Calculate text width in pixels."""
        if not text:
            return 0.0
        # Use getlength for precise width calculation
        return float(self._font.getlength(text))

    def generate(
        self,
        events: List[SubtitleEvent],
        output_path: Path,
        video_width: int = 1080,
        video_height: int = 1920,
    ) -> Path:
        """Generate ASS file with karaoke tags and layered highlights.

        Args:
            events: List of subtitle events
            output_path: Path to save ASS file
            video_width: Video width in pixels
            video_height: Video height in pixels

        Returns:
            Path to generated ASS file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            # Write header
            f.write(self._generate_header(video_width, video_height))

            # Write events
            f.write("\n[Events]\n")
            f.write("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

            for event in events:
                if self.style.use_box_highlight:
                    # Layer 0: Static, pale background text
                    f.write(self._generate_layer0_line(event) + "\n")
                    
                    # Layer 1 & 2: Word-by-word highlights
                    for i in range(len(event.words)):
                        # Layer 1: Pink rounded box drawing
                        f.write(self._generate_layer1_box_line(event, i, video_width, video_height) + "\n")
                        # Layer 2: White text with black outline
                        f.write(self._generate_layer2_word_line(event, i, video_width, video_height) + "\n")
                else:
                    # Classic karaoke style
                    dialogue_line = self._generate_dialogue(event)
                    f.write(dialogue_line + "\n")

        return output_path

    def _generate_header(self, video_width: int, video_height: int) -> str:
        """Generate ASS file header with styles."""
        # Default style (Layer 0 or Classic)
        # MarginV is taken from self.style
        header = f"""[Script Info]
Title: Karaoke Subtitles
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {video_width}
PlayResY: {video_height}

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{self.style.font_name},{self.style.font_size},{self.style.inactive_color},{self.style.secondary_color},{self.style.outline_color},{self.style.back_color},1,0,0,0,100,100,0,0,1,3.0,0.0,{self.style.alignment},{self.style.margin_l},{self.style.margin_r},{self.style.margin_v},1
Style: Highlight,{self.style.font_name},{self.style.font_size},{self.style.primary_color},{self.style.secondary_color},{self.style.outline_color},{self.style.back_color},1,0,0,0,100,100,0,0,1,{self.style.outline_width},0.0,{self.style.alignment},{self.style.margin_l},{self.style.margin_r},{self.style.margin_v},1
"""
        return header

    def _generate_layer0_line(self, event: SubtitleEvent) -> str:
        """Generate background text line (Layer 0)."""
        start = self._format_timestamp(event.start_time_ms)
        end = self._format_timestamp(event.end_time_ms)
        
        # Plain text without tags for the background layer
        text = " ".join([w.text for w in event.words])
        if self.style.use_uppercase:
            text = text.upper()
        return f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}"

    def _generate_layer1_box_line(
        self, event: SubtitleEvent, active_index: int, video_width: int, video_height: int
    ) -> str:
        """Generate a pink rounded box drawing (Layer 1)."""
        word = event.words[active_index]
        start = self._format_timestamp(word.audio_offset_ms)
        end = self._format_timestamp(word.audio_offset_ms + word.duration_ms)
        
        # Calculate box coordinates relative to line center
        full_text = " ".join([w.text for w in event.words])
        if self.style.use_uppercase:
            full_text = full_text.upper()
            
        full_width = self._get_text_width(full_text)
        
        # Get start position of the active word
        prefix_words = [w.text for w in event.words[:active_index]]
        prefix_text = " ".join(prefix_words)
        if prefix_words:
            prefix_text += " "
        if self.style.use_uppercase:
            prefix_text = prefix_text.upper()
        
        word_text = event.words[active_index].text
        if self.style.use_uppercase:
            word_text = word_text.upper()
            
        x_start = self._get_text_width(prefix_text)
        word_width = self._get_text_width(word_text)
        
        # Offset relative to center (Alignment 2)
        relative_x = x_start - (full_width / 2) + (word_width / 2)
        
        # Add padding
        padding = 10 # Manual padding for the box
        rect_width = word_width + (padding * 2)
        rect_height = self.style.font_size * 1.2
        radius = self.style.box_radius
        
        # Drawing tag \p1 using m, l, b (bezier)
        drawing = self._generate_rounded_rect_path(rect_width, rect_height, radius)
        
        # Calculate absolute screen coordinates
        # Alignment 2 is bottom-center
        base_x = video_width / 2
        base_y = video_height - self.style.margin_v
        
        abs_x = base_x + relative_x
        # Visual adjustment: boxes need to be slightly higher than the baseline
        abs_y = base_y - (self.style.font_size * 0.45)
        
        pos_tag = f"\\an5\\pos({abs_x:.1f},{abs_y:.1f})"
        color_tag = f"\\1c{self.style.highlight_color}\\bord0\\shad0"
        blur_tag = f"\\be{self.style.box_blur}" if self.style.box_blur > 0 else ""
        
        return f"Dialogue: 1,{start},{end},Highlight,,0,0,0,,{{{pos_tag}{color_tag}{blur_tag}\\p1}}{drawing}{{\\p0}}"

    def _generate_layer2_word_line(
        self, event: SubtitleEvent, active_index: int, video_width: int, video_height: int
    ) -> str:
        """Generate a single word text line (Layer 2) with outline."""
        word = event.words[active_index]
        start = self._format_timestamp(word.audio_offset_ms)
        end = self._format_timestamp(word.audio_offset_ms + word.duration_ms)
        
        # For the text line, we ALSO use \pos to ensure it's exactly aligned with the box
        # and doesn't shift due to leading/trailing space transparency
        full_text = " ".join([w.text for w in event.words])
        if self.style.use_uppercase:
            full_text = full_text.upper()
        full_width = self._get_text_width(full_text)
        
        base_x = video_width / 2
        base_y = video_height - self.style.margin_v
        
        # We place the WHOLE line at the base position, but only the active word is visible
        pos_tag = f"\\an2\\pos({base_x:.1f},{base_y:.1f})"
        
        parts = []
        for i, w in enumerate(event.words):
            word_text = w.text.upper() if self.style.use_uppercase else w.text
            if i == active_index:
                # Active word: white text with black outline
                parts.append(word_text)
            else:
                # Inactive word: completely transparent
                parts.append(f"{{\\alpha&HFF&}}{word_text}{{\\alpha&H00&}}")
            
            if i < len(event.words) - 1:
                parts.append(f"{{\\alpha&HFF&}} {{\\alpha&H00&}}")
                
        text = "".join(parts)
        return f"Dialogue: 2,{start},{end},Highlight,,0,0,0,,{{{pos_tag}}}{text}"

    def _generate_rounded_rect_path(self, width: float, height: float, r: float) -> str:
        """Generate ASS drawing path for a rounded rectangle.
        
        Centered at (0,0).
        """
        w = width / 2
        h = height / 2
        
        # Start at top edge
        # m x y (move)
        # l x y (line)
        # b x1 y1 x2 y2 x3 y3 (cubic bezier)
        
        # Simplification: if radius is too large, cap it
        r = min(r, w, h)
        
        path = [
            f"m {-w+r} {-h}",                   # Top left start
            f"l {w-r} {-h}",                    # Top edge
            f"b {w} {-h} {w} {-h} {w} {-h+r}",  # Top right corner
            f"l {w} {h-r}",                     # Right edge
            f"b {w} {h} {w} {h} {w-r} {h}",     # Bottom right corner
            f"l {-w+r} {h}",                    # Bottom edge
            f"b {-w} {h} {-w} {h} {-w} {h-r}",  # Bottom left corner
            f"l {-w} {-h+r}",                   # Left edge
            f"b {-w} {-h} {-w} {-h} {-w+r} {-h}" # Top left corner back
        ]
        return " ".join(path)

    def _generate_dialogue(self, event: SubtitleEvent) -> str:
        """Generate classic karaoke dialogue line."""
        start = self._format_timestamp(event.start_time_ms)
        end = self._format_timestamp(event.end_time_ms)
        karaoke_text = self._generate_karaoke_tags(event)
        return f"Dialogue: 0,{start},{end},Default,,0,0,0,,{karaoke_text}"

    def _format_timestamp(self, ms: int) -> str:
        """Format milliseconds to ASS timestamp format."""
        hours = ms // 3600000
        ms %= 3600000
        minutes = ms // 60000
        ms %= 60000
        seconds = ms // 1000
        centiseconds = (ms % 1000) // 10
        return f"{hours}:{minutes:02d}:{seconds:02d}.{centiseconds:02d}"

    def _generate_karaoke_tags(self, event: SubtitleEvent) -> str:
        """Generate classic karaoke tags."""
        parts = []
        for i, word in enumerate(event.words):
            duration_cs = word.duration_ms // 10
            if self._is_punctuation(word.text):
                parts.append(f"{{\\kf0}}{word.text}")
            else:
                parts.append(f"{{\\kf{duration_cs}}}{word.text}")
            if i < len(event.words) - 1:
                next_word = event.words[i + 1]
                if not self._is_punctuation(next_word.text):
                    parts.append(" ")
        return "".join(parts)

    def _is_punctuation(self, text: str) -> bool:
        """Check if text is punctuation."""
        cleaned = re.sub(r"[\w\s]", "", text)
        return len(cleaned) > 0 and len(cleaned) == len(text)
