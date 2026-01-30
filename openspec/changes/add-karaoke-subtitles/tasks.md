# Tasks: Add Karaoke Subtitles

## 1. Foundation & Infrastructure

- [ ] 1.1 Create module structure `src/subtitles/` with `__init__.py`
- [ ] 1.2 Create `models.py` with Pydantic models (`WordBoundary`, `SubtitleEvent`, `TTSResult`, `KaraokeResult`, `KaraokeConfig`)
- [ ] 1.3 Create `storage.py` with `StorageManager` (content hashing, directory management)
- [ ] 1.4 Add `data/audio/` to `.gitignore` and create placeholder
- [ ] 1.5 Add dependencies to `pyproject.toml`: `edge-tts>=6.1.0`

## 2. Text Processing

- [ ] 2.1 Create `normalizer.py` with `TextNormalizer` class
- [ ] 2.2 Implement text normalization rules (whitespace, quotes, dashes, control chars)
- [ ] 2.3 Implement tokenization (words vs punctuation)
- [ ] 2.4 Write unit tests for `TextNormalizer` (`tests/subtitles/test_normalizer.py`)

## 3. TTS Engine

- [ ] 3.1 Create `tts_engine.py` with `TTSEngine` class
- [ ] 3.2 Implement Edge TTS synthesis with word-boundary event capture
- [ ] 3.3 Implement timing interpolation for missing word boundaries
- [ ] 3.4 Add configuration for language and voice selection
- [ ] 3.5 Write unit tests for `TTSEngine` (mock edge-tts, test boundary parsing)

## 4. Subtitle Generation

- [ ] 4.1 Create `segmenter.py` with `SubtitleSegmenter` class
- [ ] 4.2 Implement single-line segmentation algorithm
- [ ] 4.3 Create `ass_generator.py` with `ASSGenerator` class
- [ ] 4.4 Implement ASS header generation with customizable styles
- [ ] 4.5 Implement karaoke tag formatting (`\kf` with centisecond durations)
- [ ] 4.6 Handle punctuation (zero-duration, no highlight)
- [ ] 4.7 Write unit tests for segmenter and ASS generator

## 5. Video Rendering

- [ ] 5.1 Create `renderer.py` with `KaraokeRenderer` class
- [ ] 5.2 Implement video probing (duration, dimensions via ffprobe)
- [ ] 5.3 Implement 9:16 aspect ratio cropping (center crop)
- [ ] 5.4 Implement video looping/trimming to match audio duration
- [ ] 5.5 Implement subtitle burning via FFmpeg `subtitles` filter
- [ ] 5.6 Implement audio mixing with video
- [ ] 5.7 Write integration tests for karaoke renderer (test with small fixtures)

## 6. Pipeline & CLI

- [ ] 6.1 Create `pipeline.py` with `KaraokePipeline` class
- [ ] 6.2 Implement full orchestration (normalize → TTS → segment → ASS → compose)
- [ ] 6.3 Implement artifact caching (skip TTS if hash exists)
- [ ] 6.4 Implement logging with key metrics (duration, word count, segment count, interpolation %)
- [ ] 6.5 Create `__main__.py` with CLI using Typer
- [ ] 6.6 Implement `create` command with all options
- [ ] 6.7 Write end-to-end test for CLI

## 7. Configuration & Styles

- [ ] 7.1 Create `styles.py` with default `SubtitleStyle` configuration
- [ ] 7.2 Implement JSON config loading for custom styles
- [ ] 7.3 Create example style config file in `examples/subtitle_style.json`
- [ ] 7.4 Document available style options

## 8. Documentation

- [ ] 8.1 Create `README.md` for subtitles module with usage examples
- [ ] 8.2 Add docstrings to all public functions and classes
- [ ] 8.3 Update project README.md with new module reference

## 9. Verification

- [ ] 9.1 Run all unit tests: `pytest tests/subtitles/ -v`
- [ ] 9.2 Test with Spanish script: verify word highlighting syncs with audio
- [ ] 9.3 Test with different aspect ratio background: verify correct cropping
- [ ] 9.4 Test with short background video: verify looping works
- [ ] 9.5 Test with long background video: verify trimming works
- [ ] 9.6 Visual inspection of final video output
- [ ] 9.7 Test CLI with various option combinations

---

## Dependencies

| Task | Depends On |
|------|------------|
| 2.x Text Processing | 1.x Foundation |
| 3.x TTS Engine | 1.x Foundation, 2.x Text Processing |
| 4.x Subtitle Generation | 3.x TTS Engine |
| 5.x Video Composition | 4.x Subtitle Generation |
| 6.x Pipeline | All above |
| 7.x Configuration | 1.x Foundation |
| 8.x Documentation | 6.x Pipeline (can be parallel) |
| 9.x Verification | 6.x Pipeline |

## Parallelizable Work

- Tasks 2.x and 7.x can run in parallel after 1.x
- Tasks 4.3-4.6 (ASS) can run in parallel with 4.1-4.2 (Segmenter) after 3.x
- Task 8.x can progress in parallel with later implementation tasks

---

## Future Scope (Not Implemented)

> [!NOTE]
> These items are documented for future reference but NOT part of this change.

- **Batch Mode**: `python -m src.subtitles batch --input-dir scripts/ --bg bg.mp4 --output-dir output/`
- **Style Presets**: Built-in presets like `neon`, `minimal`, `bold`
- **Music Mixing**: Add optional `--music` flag for background track
- **Preview Mode**: Quick preview without full video encoding
