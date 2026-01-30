"""CLI for karaoke subtitles module."""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler

from .models import KaraokeConfig, SubtitleStyle
from .pipeline import KaraokePipeline

console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, console=console)],
)

logger = logging.getLogger(__name__)


def main(
    script: Path = typer.Option(..., "--script", help="Path to script text file"),
    bg: Path = typer.Option(..., "--bg", help="Path to background video"),
    output: Path = typer.Option(..., "--output", help="Path to output video"),
    lang: str = typer.Option("es-ES", "--lang", help="Language code (e.g., es-ES, en-US)"),
    voice: Optional[str] = typer.Option(
        None, "--voice", help="Voice name (e.g., es-ES-ElviraNeural)"
    ),
    style_config: Optional[Path] = typer.Option(
        None, "--style-config", help="Path to style configuration JSON"
    ),
):
    """Create a karaoke video with TTS audio and synced subtitles.

    Example:
        python -m src.subtitles --script script.txt --bg bg.mp4 --output final.mp4
    """
    # Validate input files
    if not script.exists():
        console.print(f"[red]Error: Script file not found: {script}[/red]")
        raise typer.Exit(1)

    if not bg.exists():
        console.print(f"[red]Error: Background video not found: {bg}[/red]")
        raise typer.Exit(1)

    # Build configuration
    config = KaraokeConfig(language=lang)

    # Set voice (use default for language if not specified)
    if voice:
        config.voice = voice
    else:
        # Default voices per language
        default_voices = {
            "es-ES": "es-ES-ElviraNeural",
            "en-US": "en-US-AriaNeural",
            "en-GB": "en-GB-SoniaNeural",
            "fr-FR": "fr-FR-DeniseNeural",
            "de-DE": "de-DE-KatjaNeural",
        }
        config.voice = default_voices.get(lang, f"{lang}-Standard-A")

    # Load custom style if provided
    if style_config:
        if not style_config.exists():
            console.print(f"[red]Error: Style config not found: {style_config}[/red]")
            raise typer.Exit(1)

        try:
            with open(style_config, "r", encoding="utf-8") as f:
                style_data = json.load(f)
            config.style = SubtitleStyle(**style_data)
            console.print(f"[green]Loaded custom style from {style_config}[/green]")
        except Exception as e:
            console.print(f"[red]Error loading style config: {e}[/red]")
            raise typer.Exit(1)

    # Run pipeline
    console.print("[bold]Starting karaoke video generation...[/bold]")
    console.print(f"Script: {script}")
    console.print(f"Background: {bg}")
    console.print(f"Output: {output}")
    console.print(f"Language: {config.language}")
    console.print(f"Voice: {config.voice}")

    pipeline = KaraokePipeline(config)

    # Run async pipeline
    result = asyncio.run(pipeline.create(script, bg, output))

    # Display result
    if result.success:
        console.print("\n[bold green]✓ Video created successfully![/bold green]")
        console.print(f"Output: {result.output_path}")
        console.print(f"Artifacts: {result.artifact_dir}")
        console.print(f"\nStats:")
        console.print(f"  Duration: {result.audio_duration_ms / 1000:.2f}s")
        console.print(f"  Words: {result.word_count}")
        console.print(f"  Segments: {result.segment_count}")
        if result.interpolated_words_pct > 0:
            console.print(
                f"  Interpolated: {result.interpolated_words_pct:.1f}%",
                style="yellow",
            )
    else:
        console.print("\n[bold red]✗ Video generation failed[/bold red]")
        console.print(f"Error: {result.error}")
        raise typer.Exit(1)


if __name__ == "__main__":
    typer.run(main)

