# Change: Add Karaoke Subtitles Module

## Why

QuickTok needs to generate TikTok-ready videos with synchronized text-to-speech audio and karaoke-style subtitles (progressive word highlighting). This capability is essential for creating engaging short-form content with clear visual text that highlights word-by-word as the narration plays, which significantly increases viewer retention and accessibility.

Currently, video creation and audio generation are conceptualized separately in the roadmap. This change introduces a dedicated, independent module that handles the complete pipeline: text normalization → TTS synthesis with word-boundary timings → ASS subtitle generation with karaoke effects → final video assembly with burned-in subtitles.

## What Changes

### New Module: `src/subtitles/`

A standalone module for generating videos with TTS audio and karaoke subtitles:

- **Text Normalizer**: Cleans and prepares input text for TTS (whitespace, quotes, dashes, number/abbreviation rules).
- **TTS Engine**: Synthesizes speech using Edge TTS with word-boundary event capture (`audioOffset`, `duration`).
- **Subtitle Generator**: Creates ASS files with karaoke tags (`\K`, `\kf`) for progressive word highlighting.
- **Video Renderer**: Assembles final video by combining background video, TTS audio, and burned-in subtitles via FFmpeg.
- **Style Configuration**: Customizable subtitle appearance (font, color, size, position, highlight color) with sensible defaults.

### New Data Structure: `data/audio/`

Organized storage for TTS artifacts:
```
data/audio/
└── {content_hash}/           # Hash of input text for uniqueness
    ├── voice.mp3             # Synthesized audio
    ├── word_boundaries.json  # Word timing data
    ├── subs.ass              # Generated ASS subtitles
    └── metadata.json         # Generation parameters
```

### CLI Interface

```bash
python -m src.subtitles --script script_es.txt --bg bg.mp4 --output final.mp4
python -m src.subtitles --script script_es.txt --bg bg.mp4 --lang es-ES --voice ElviraNeural
python -m src.subtitles --script script_es.txt --bg bg.mp4 --style-config styles.json
```

### Key Features

1. **Single-Line Subtitle Display**: Text is segmented to show one line at a time (no two-line wrapping).
2. **Karaoke Highlighting**: Words are progressively filled (painted) based on TTS timing data.
3. **Punctuation Handling**: Punctuation marks are displayed but not highlighted.
4. **Video Duration Policy**: Audio duration becomes the target; background video is looped or trimmed accordingly.
5. **Aspect Ratio Enforcement**: Background video is cropped (not resized) to 9:16 if needed.
6. **Multi-Language Support**: Configurable language and voice selection for Edge TTS.
7. **Timing Interpolation**: Fallback interpolation for words missing timing data.

## Impact

- **Affected specs**: None (new capability)
- **New specs**: `subtitles`
- **Affected code**: None (new module)
- **New directories**: `src/subtitles/`, `data/audio/`
- **Dependencies**: `edge-tts`, `ffmpeg-python` (already planned), `hashlib` (stdlib)

## Future Considerations (Not in Scope)

- Batch mode for multiple scripts (documented but not implemented initially)
- LLM-generated scripts integration
- Music background mixing
- Auto-generated backgrounds from images
