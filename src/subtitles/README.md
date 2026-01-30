# Karaoke Subtitles Module

Generate TikTok-ready videos with synchronized TTS audio and karaoke-style subtitles.

## Features

- 🎤 Text-to-speech synthesis using Edge TTS
- 🎬 Word-accurate karaoke subtitle highlighting
- 📐 Automatic 9:16 aspect ratio cropping
- 🔄 Video looping/trimming to match audio duration
- 🎨 Customizable subtitle styles
- 💾 Artifact caching for faster regeneration
- 🌍 Multi-language support

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

Ensure FFmpeg is installed:

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt-get install ffmpeg

# Windows
# Download from https://ffmpeg.org/download.html
```

## Quick Start

```bash
python -m src.subtitles \
  --script script.txt \
  --bg background.mp4 \
  --output final.mp4
```

## Usage

### Basic Command

```bash
python -m src.subtitles \
  --script <script_file> \
  --bg <background_video> \
  --output <output_video>
```

### Custom Language and Voice

```bash
python -m src.subtitles \
  --script script_es.txt \
  --bg bg.mp4 \
  --output final.mp4 \
  --lang es-ES \
  --voice es-ES-ElviraNeural
```

### Custom Style

```bash
python -m src.subtitles \
  --script script.txt \
  --bg bg.mp4 \
  --output final.mp4 \
  --style-config examples/subtitle_style.json
```

## Configuration

### Subtitle Styles

Customize subtitle appearance using a JSON configuration file:

```json
{
  "font_name": "Arial",
  "font_size": 48,
  "primary_color": "&H00FFFFFF",
  "secondary_color": "&H0000FFFF",
  "outline_color": "&H00000000",
  "back_color": "&H80000000",
  "outline_width": 2.0,
  "shadow_depth": 1.0,
  "alignment": 2,
  "margin_v": 60,
  "margin_l": 40,
  "margin_r": 40
}
```

See `examples/subtitle_style.json` for a complete example.

### ASS Color Format

Colors in ASS format use `&HAABBGGRR` (hexadecimal, reversed RGB):
- `&H00FFFFFF` = White
- `&H0000FFFF` = Yellow
- `&H000000FF` = Red
- `&H00FF0000` = Blue

Alpha channel (AA) controls transparency:
- `&H00` = Opaque
- `&H80` = Semi-transparent
- `&HFF` = Transparent

### Supported Languages

Common language codes and default voices:

| Language | Code | Default Voice |
|----------|------|---------------|
| Spanish | `es-ES` | `es-ES-ElviraNeural` |
| English (US) | `en-US` | `en-US-AriaNeural` |
| English (UK) | `en-GB` | `en-GB-SoniaNeural` |
| French | `fr-FR` | `fr-FR-DeniseNeural` |
| German | `de-DE` | `de-DE-KatjaNeural` |

For a complete list of voices, see [Edge TTS voices](https://github.com/rany2/edge-tts#list-voices).

## How It Works

1. **Text Normalization**: Cleans and prepares input text for TTS
2. **TTS Synthesis**: Generates audio with word-boundary timing data
3. **Segmentation**: Splits words into single-line subtitle events
4. **ASS Generation**: Creates ASS subtitle file with karaoke tags
5. **Video Rendering**: Assembles final video with FFmpeg

### Pipeline Flow

```
script.txt → normalize → TTS (Edge) → segment → ASS → FFmpeg → final.mp4
                                                          ↑
                                                     bg.mp4
```

## Output Structure

Artifacts are stored in `data/audio/{content_hash}/`:

```
data/audio/
└── a1b2c3d4e5f6/          # Content hash
    ├── voice.mp3          # Synthesized audio
    ├── word_boundaries.json
    ├── subs.ass           # ASS subtitle file
    └── metadata.json      # Generation config
```

## Troubleshooting

### FFmpeg not found

Ensure FFmpeg is installed and in your PATH:

```bash
ffmpeg -version
```

### Edge TTS connection issues

If synthesis fails, try:
1. Check your internet connection
2. Verify the voice name is correct
3. Try a different voice

### Subtitle timing issues

If subtitles don't sync properly:
1. Check `word_boundaries.json` for timing data
2. Review `metadata.json` for interpolation warnings
3. Try a different voice or language

## Examples

### Spanish Tutorial Video

```bash
python -m src.subtitles \
  --script tutorial_es.txt \
  --bg gameplay.mp4 \
  --output tutorial.mp4 \
  --lang es-ES
```

### English with Custom Style

```bash
python -m src.subtitles \
  --script story_en.txt \
  --bg background.mp4 \
  --output story.mp4 \
  --lang en-US \
  --voice en-US-GuyNeural \
  --style-config styles/neon.json
```

## API Usage

You can also use the module programmatically:

```python
import asyncio
from pathlib import Path
from src.subtitles import KaraokePipeline, KaraokeConfig

async def main():
    config = KaraokeConfig(
        language="es-ES",
        voice="es-ES-ElviraNeural"
    )
    
    pipeline = KaraokePipeline(config)
    
    result = await pipeline.create(
        script_path=Path("script.txt"),
        background_video=Path("bg.mp4"),
        output_path=Path("final.mp4")
    )
    
    if result.success:
        print(f"Video created: {result.output_path}")
        print(f"Duration: {result.audio_duration_ms / 1000:.2f}s")
    else:
        print(f"Error: {result.error}")

asyncio.run(main())
```

## License

Part of the QuickTok project.
