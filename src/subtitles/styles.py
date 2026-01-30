"""Default subtitle styles and style loading."""

import json
from pathlib import Path

from .models import SubtitleStyle


def load_style_from_json(path: Path) -> SubtitleStyle:
    """Load subtitle style from JSON file.

    Args:
        path: Path to JSON style configuration

    Returns:
        SubtitleStyle instance

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    if not path.exists():
        raise FileNotFoundError(f"Style configuration not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    return SubtitleStyle(**data)


# Default styles
DEFAULT_STYLE = SubtitleStyle()

NEON_STYLE = SubtitleStyle(
    font_name="Arial",
    font_size=110,
    primary_color="&H00FFFFFF",  # White
    secondary_color="&H00FF00FF",  # Magenta/Pink
    outline_color="&H00FF00FF",  # Magenta outline
    back_color="&H80000000",
    outline_width=4.0,
    shadow_depth=3.0,
    margin_v=220,
)

MINIMAL_STYLE = SubtitleStyle(
    font_name="Helvetica",
    font_size=80,
    primary_color="&H00FFFFFF",  # White
    secondary_color="&H0000FFFF",  # Yellow
    outline_color="&H00000000",  # Black
    back_color="&H00000000",  # Transparent
    outline_width=2.5,
    shadow_depth=1.0,
    margin_v=150,
)

BOLD_STYLE = SubtitleStyle(
    font_name="Arial",
    font_size=120,
    primary_color="&H00FFFFFF",  # White
    secondary_color="&H000000FF",  # Red
    outline_color="&H00000000",  # Black
    back_color="&HA0000000",  # Semi-transparent
    outline_width=6.0,
    shadow_depth=4.0,
    margin_v=250,
)
