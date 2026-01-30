"""Main karaoke pipeline orchestration."""

import logging
from pathlib import Path

from .ass_generator import ASSGenerator
from .models import KaraokeConfig, KaraokeResult
from .normalizer import TextNormalizer
from .renderer import KaraokeRenderer
from .segmenter import SubtitleSegmenter
from .storage import StorageManager
from .tts_engine import TTSEngine

logger = logging.getLogger(__name__)


class KaraokePipeline:
    """Orchestrates the complete karaoke video generation process."""

    def __init__(self, config: KaraokeConfig = None):
        """Initialize pipeline.

        Args:
            config: Karaoke configuration
        """
        self.config = config or KaraokeConfig()

        # Initialize components
        self.normalizer = TextNormalizer(self.config.normalization)
        self.tts_engine = TTSEngine(
            language=self.config.language,
            voice=self.config.voice,
        )
        self.segmenter = SubtitleSegmenter(self.config.segmentation)
        self.ass_generator = ASSGenerator(self.config.style)
        self.renderer = KaraokeRenderer(self.config.renderer)
        self.storage = StorageManager()

    async def create(
        self,
        script_path: Path,
        background_video: Path,
        output_path: Path,
    ) -> KaraokeResult:
        """Execute full pipeline: text → TTS → ASS → video.

        Args:
            script_path: Path to script text file
            background_video: Path to background video
            output_path: Path to output video

        Returns:
            KaraokeResult with generation details
        """
        try:
            logger.info("Starting karaoke pipeline")

            # 1. Read and normalize script text
            logger.info(f"Reading script from {script_path}")
            with open(script_path, "r", encoding="utf-8") as f:
                text = f.read()

            normalized_text = self.normalizer.normalize(text)
            logger.info(f"Normalized text: {len(normalized_text)} chars")

            # 2. Get artifact directory
            artifact_dir = self.storage.get_artifact_dir(normalized_text)
            logger.info(f"Artifact directory: {artifact_dir}")

            # 3. Synthesize TTS with word boundaries (or reuse cached)
            audio_path = artifact_dir / "voice.mp3"

            if audio_path.exists():
                logger.info("Using cached TTS audio")
                # Load cached word boundaries
                import json

                boundaries_path = artifact_dir / "word_boundaries.json"
                with open(boundaries_path, "r", encoding="utf-8") as f:
                    boundaries_data = json.load(f)

                from .models import WordBoundary

                word_boundaries = [
                    WordBoundary(
                        text=wb["text"],
                        audio_offset_ms=wb["audio_offset_ms"],
                        duration_ms=wb["duration_ms"],
                    )
                    for wb in boundaries_data
                ]

                # Calculate total duration
                if word_boundaries:
                    total_duration_ms = (
                        word_boundaries[-1].audio_offset_ms
                        + word_boundaries[-1].duration_ms
                    )
                else:
                    total_duration_ms = 0
            else:
                logger.info("Synthesizing TTS audio")
                tts_result = await self.tts_engine.synthesize(normalized_text, audio_path)
                word_boundaries = tts_result.word_boundaries
                total_duration_ms = tts_result.total_duration_ms

            logger.info(
                f"TTS complete: {len(word_boundaries)} words, {total_duration_ms}ms"
            )

            # 4. Segment words into subtitle events
            logger.info("Segmenting words into subtitle events")
            subtitle_events = self.segmenter.segment(word_boundaries)
            logger.info(f"Created {len(subtitle_events)} subtitle events")

            # 5. Generate ASS file
            logger.info("Generating ASS subtitle file")
            ass_path = artifact_dir / "subs.ass"
            self.ass_generator.generate(
                subtitle_events,
                ass_path,
                video_width=self.config.renderer.target_width,
                video_height=self.config.renderer.target_height,
            )
            logger.info(f"ASS file generated: {ass_path}")

            # 6. Render final video
            logger.info("Rendering final video")
            self.renderer.render_video(
                background_video=background_video,
                audio=audio_path,
                subtitles=ass_path,
                output=output_path,
                target_duration_ms=total_duration_ms,
            )
            logger.info(f"Video rendered: {output_path}")

            # 7. Calculate statistics
            interpolated_count = 0  # TODO: Track from TTS engine
            interpolated_pct = (
                (interpolated_count / len(word_boundaries) * 100)
                if word_boundaries
                else 0.0
            )

            # Save metadata
            self.storage.save_metadata(
                artifact_dir,
                config={
                    "language": self.config.language,
                    "voice": self.config.voice,
                },
                stats={
                    "audio_duration_ms": total_duration_ms,
                    "word_count": len(word_boundaries),
                    "segment_count": len(subtitle_events),
                    "interpolated_words_pct": interpolated_pct,
                },
            )

            return KaraokeResult(
                success=True,
                output_path=output_path,
                artifact_dir=artifact_dir,
                audio_duration_ms=total_duration_ms,
                word_count=len(word_boundaries),
                segment_count=len(subtitle_events),
                interpolated_words_pct=interpolated_pct,
            )

        except Exception as e:
            logger.error(f"Pipeline failed: {e}", exc_info=True)
            return KaraokeResult(
                success=False,
                output_path=None,
                artifact_dir=artifact_dir if "artifact_dir" in locals() else Path(),
                audio_duration_ms=0,
                word_count=0,
                segment_count=0,
                interpolated_words_pct=0.0,
                error=str(e),
            )
