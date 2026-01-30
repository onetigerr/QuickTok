"""Video rendering with subtitle burning."""

import json
import logging
import subprocess
from pathlib import Path

from .models import RendererConfig

logger = logging.getLogger(__name__)


class KaraokeRenderer:
    """Renders final video with audio and burned-in subtitles."""

    def __init__(self, config: RendererConfig = None):
        """Initialize renderer.

        Args:
            config: Renderer configuration
        """
        self.config = config or RendererConfig()

    def render_video(
        self,
        background_video: Path,
        audio: Path,
        subtitles: Path,
        output: Path,
        target_duration_ms: int,
    ) -> Path:
        """Compose final video with audio and burned-in subtitles.

        Args:
            background_video: Path to background video
            audio: Path to audio file
            subtitles: Path to ASS subtitle file
            output: Path to output video
            target_duration_ms: Target duration in milliseconds

        Returns:
            Path to rendered video
        """
        # Probe background video
        video_info = self._probe_video(background_video)
        video_duration_ms = int(float(video_info["duration"]) * 1000)
        width = int(video_info["width"])
        height = int(video_info["height"])

        logger.info(
            f"Background video: {width}x{height}, duration: {video_duration_ms}ms"
        )
        logger.info(f"Target duration: {target_duration_ms}ms")

        # Prepare FFmpeg command
        output.parent.mkdir(parents=True, exist_ok=True)

        # Build video filter
        vf_parts = []

        # Crop to 9:16 if needed
        target_aspect = self.config.target_height / self.config.target_width  # 16/9
        current_aspect = height / width

        if abs(current_aspect - target_aspect) > 0.01:  # Not already 9:16
            # Center crop to 9:16
            crop_width = int(height / target_aspect)
            crop_x = (width - crop_width) // 2
            vf_parts.append(f"crop={crop_width}:{height}:{crop_x}:0")
            logger.info(f"Cropping to 9:16: {crop_width}x{height}")

        # Scale to target resolution
        vf_parts.append(f"scale={self.config.target_width}:{self.config.target_height}")

        # Burn subtitles using filename parameter
        # Use absolute path with forward slashes (Unix style)
        subtitles_path = str(subtitles.absolute()).replace("\\", "/")
        vf_parts.append(f"subtitles=filename='{subtitles_path}'")

        vf = ",".join(vf_parts)

        # Determine if we need to loop or trim
        target_duration_sec = target_duration_ms / 1000

        cmd = ["ffmpeg", "-y"]

        # Loop video if it's shorter than audio
        if video_duration_ms < target_duration_ms:
            cmd.extend(["-stream_loop", "-1"])
            logger.info("Looping video to match audio duration")

        cmd.extend(
            [
                "-i",
                str(background_video),
                "-i",
                str(audio),
                "-vf",
                vf,
                "-c:v",
                self.config.video_codec,
                "-preset",
                self.config.preset,
                "-crf",
                str(self.config.crf),
                "-c:a",
                self.config.audio_codec,
                "-shortest",
                "-t",
                str(target_duration_sec),
                str(output),
            ]
        )

        logger.info(f"Running FFmpeg: {' '.join(cmd)}")

        # Run FFmpeg
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )

        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed with code {result.returncode}")

        logger.info(f"Video rendered successfully: {output}")
        return output

    def _probe_video(self, video_path: Path) -> dict:
        """Probe video file for metadata.

        Args:
            video_path: Path to video file

        Returns:
            Dictionary with video metadata
        """
        cmd = [
            "ffprobe",
            "-v",
            "quiet",
            "-print_format",
            "json",
            "-show_streams",
            "-select_streams",
            "v:0",
            str(video_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)

        if not data.get("streams"):
            raise ValueError(f"No video stream found in {video_path}")

        stream = data["streams"][0]

        return {
            "width": stream.get("width"),
            "height": stream.get("height"),
            "duration": stream.get("duration") or data.get("format", {}).get("duration"),
        }
