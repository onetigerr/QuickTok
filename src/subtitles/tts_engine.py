"""TTS engine using Edge TTS with word-boundary capture."""

import asyncio
import json
import logging
from pathlib import Path
from typing import List

import edge_tts

from .models import TTSResult, WordBoundary

logger = logging.getLogger(__name__)


class TTSEngine:
    """TTS engine for speech synthesis with word-boundary timing."""

    def __init__(
        self,
        language: str = "es-ES",
        voice: str = "es-ES-ElviraNeural",
        rate: str = "+0%",
        volume: str = "+0%",
    ):
        """Initialize TTS engine.

        Args:
            language: Language code (e.g., "es-ES", "en-US")
            voice: Voice name (e.g., "es-ES-ElviraNeural")
            rate: Speech rate adjustment
            volume: Volume adjustment
        """
        self.language = language
        self.voice = voice
        self.rate = rate
        self.volume = volume
        self._word_boundaries: List[dict] = []

    async def synthesize(self, text: str, output_path: Path) -> TTSResult:
        """Synthesize speech with word-boundary capture.

        Args:
            text: Text to synthesize
            output_path: Path to save audio file

        Returns:
            TTSResult with audio path and word boundaries
        """
        self._word_boundaries = []

        # Create communicate object
        communicate = edge_tts.Communicate(text, self.voice, rate=self.rate, volume=self.volume)

        # Synthesize and capture events
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
            elif chunk["type"] == "WordBoundary":
                self._word_boundaries.append(chunk)

        # Write audio to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "wb") as f:
            f.write(audio_data)

        # Convert word boundaries to WordBoundary objects
        word_boundaries = self._parse_word_boundaries()

        # Calculate total duration
        if word_boundaries:
            total_duration_ms = (
                word_boundaries[-1].audio_offset_ms + word_boundaries[-1].duration_ms
            )
        else:
            # Fallback: Edge TTS no longer returns WordBoundary events
            # Generate synthetic boundaries based on audio duration
            logger.warning("No word boundaries received from Edge TTS, generating synthetic boundaries")
            total_duration_ms = self._get_audio_duration_ms(output_path)
            word_boundaries = self._generate_synthetic_boundaries(text, total_duration_ms)

        # Save word boundaries to JSON
        boundaries_path = output_path.parent / "word_boundaries.json"
        with open(boundaries_path, "w", encoding="utf-8") as f:
            json.dump(
                [
                    {
                        "text": wb.text,
                        "audio_offset_ms": wb.audio_offset_ms,
                        "duration_ms": wb.duration_ms,
                    }
                    for wb in word_boundaries
                ],
                f,
                indent=2,
                ensure_ascii=False,
            )

        return TTSResult(
            audio_path=output_path,
            word_boundaries=word_boundaries,
            total_duration_ms=total_duration_ms,
        )

    def _parse_word_boundaries(self) -> List[WordBoundary]:
        """Parse word boundary events from Edge TTS.

        Returns:
            List of WordBoundary objects
        """
        boundaries = []

        for event in self._word_boundaries:
            # Edge TTS provides offset and duration in 100-nanosecond units
            # Convert to milliseconds
            offset_100ns = event.get("offset", 0)
            duration_100ns = event.get("duration", 0)

            offset_ms = offset_100ns // 10000  # 100ns to ms
            duration_ms = duration_100ns // 10000

            text = event.get("text", "")

            if text:  # Only include non-empty words
                boundaries.append(
                    WordBoundary(
                        text=text,
                        audio_offset_ms=offset_ms,
                        duration_ms=duration_ms,
                    )
                )

        # Interpolate missing durations if needed
        boundaries = self._interpolate_missing_timings(boundaries)

        return boundaries

    def _interpolate_missing_timings(
        self, boundaries: List[WordBoundary]
    ) -> List[WordBoundary]:
        """Interpolate timing data for words with missing durations.

        Args:
            boundaries: List of word boundaries

        Returns:
            List of word boundaries with interpolated timings
        """
        if not boundaries:
            return boundaries

        # Count words with missing timings
        missing_count = sum(1 for wb in boundaries if wb.duration_ms == 0)

        if missing_count == 0:
            return boundaries

        # Calculate average duration from available data
        valid_durations = [wb.duration_ms for wb in boundaries if wb.duration_ms > 0]

        if not valid_durations:
            # No valid timings, use default
            avg_duration = 300  # 300ms default
            logger.warning(
                f"No valid word timings found, using default {avg_duration}ms"
            )
        else:
            avg_duration = sum(valid_durations) // len(valid_durations)

        # Interpolate missing durations
        for i, wb in enumerate(boundaries):
            if wb.duration_ms == 0:
                # Use average duration
                boundaries[i] = WordBoundary(
                    text=wb.text,
                    audio_offset_ms=wb.audio_offset_ms,
                    duration_ms=avg_duration,
                )

        interpolated_pct = (missing_count / len(boundaries)) * 100
        if interpolated_pct > 0:
            logger.warning(
                f"Interpolated {missing_count}/{len(boundaries)} words ({interpolated_pct:.1f}%)"
            )

        return boundaries

    def _get_audio_duration_ms(self, audio_path: Path) -> int:
        """Get audio file duration using ffprobe.

        Args:
            audio_path: Path to audio file

        Returns:
            Duration in milliseconds
        """
        import subprocess

        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            str(audio_path),
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            duration_sec = float(data["format"]["duration"])
            return int(duration_sec * 1000)
        except Exception as e:
            logger.error(f"Failed to get audio duration: {e}")
            # Fallback to conservative estimate
            return 2000  # 2 seconds default

    def _generate_synthetic_boundaries(
        self, text: str, total_duration_ms: int
    ) -> List[WordBoundary]:
        """Generate synthetic word boundaries by evenly distributing words across duration.

        Args:
            text: Original text
            total_duration_ms: Total audio duration in milliseconds

        Returns:
            List of synthetic word boundaries
        """
        # Import normalizer to get words
        from .normalizer import TextNormalizer

        normalizer = TextNormalizer()
        words = normalizer.get_word_tokens(text)

        if not words:
            logger.warning("No words found in text")
            return []

        # Distribute duration evenly across words
        word_duration_ms = total_duration_ms // len(words)

        boundaries = []
        current_offset = 0

        for word in words:
            boundaries.append(
                WordBoundary(
                    text=word,
                    audio_offset_ms=current_offset,
                    duration_ms=word_duration_ms,
                )
            )
            current_offset += word_duration_ms

        logger.info(
            f"Generated {len(boundaries)} synthetic word boundaries "
            f"(avg {word_duration_ms}ms per word)"
        )

        return boundaries
