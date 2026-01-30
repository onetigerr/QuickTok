---
name: video-screenshots
description: Capture screenshots from a video at specific intervals (10%, 30%, 50%, 70%, 90%) for visual analysis.
---

# Video Screenshots Skill

This skill allows the agent to visually inspect a generated video by capturing representative frames.

## Usage

When you need to verify the visual output of a video (e.g., subtitles, overlays, transitions), follow these steps:

1. **Locate the video file**: Identify the path to the video file you want to analyze.
2. **Run the capture script**: Use the provided script to generate screenshots.
   ```bash
   ./.agent/skills/video-screenshots/scripts/capture_screenshots.sh path/to/video.mp4
   ```
3. **Verify Screenshots**: The screenshots will be saved to `data/screenshots/`.
4. **Analyze**: Use the screenshots to check for:
   - Subtitle positioning and styling.
   - Video quality and aspect ratio.
   - Any visual artifacts or errors.

## Implementation Details

The skill uses `ffprobe` to determine video duration and `ffmpeg` to extract frames at 10%, 30%, 50%, 70%, and 90% of the total duration.

### FFmpeg Command Template
```bash
ffmpeg -ss [timestamp] -i [input] -frames:v 1 -q:v 2 [output]
```

## Directory Structure
- `scripts/capture_screenshots.sh`: The main automation script.
- `data/screenshots/`: Target directory for output images.
