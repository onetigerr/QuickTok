# Design: Karaoke Subtitles Module

## Context

QuickTok needs to produce TikTok-ready videos with synchronized TTS audio and karaoke-style subtitles. The module must be independent from the existing VideoCreator roadmap, allowing parallel development and flexible composition in future pipelines.

### Stakeholders
- Content creators using QuickTok for TikTok video production
- Developers extending the video creation pipeline

### Constraints
- Must use Edge TTS (free, high-quality, supports word-boundary events)
- Must produce 9:16 vertical video format
- Subtitles must be burned-in (not as separate track) for universal platform compatibility
- Must support multiple languages (Spanish primary, but configurable)

---

## Goals / Non-Goals

### Goals
- Create a standalone, reusable module for TTS + karaoke subtitles
- Provide word-accurate timing synchronization via Edge TTS word-boundary events
- Support customizable subtitle styling through configuration
- Implement robust video assembly with FFmpeg/libass
- Store intermediate artifacts for debugging and reuse

### Non-Goals
- No integration with existing VideoCreator in this change
- No LLM-based script generation
- No batch processing (documented for future)
- No music mixing or multiple audio tracks
- No automatic background generation from images

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Karaoke Subtitles Module                      │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│   ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│   │    Input     │    │   Storage    │    │       Output         │  │
│   │              │    │              │    │                      │  │
│   │ script.txt   │    │ data/audio/  │    │ final.mp4            │  │
│   │ bg.mp4       │    │   {hash}/    │    │ (with burned-in ASS) │  │
│   │ config.json  │    │              │    │                      │  │
│   └──────┬───────┘    └──────────────┘    └──────────────────────┘  │
│          │                    ▲                      ▲               │
│          ▼                    │                      │               │
│   ┌──────────────┐            │                      │               │
│   │    Text      │            │                      │               │
│   │  Normalizer  │────────────┤                      │               │
│   └──────┬───────┘            │                      │               │
│          │                    │                      │               │
│          ▼                    │                      │               │
│   ┌──────────────┐            │                      │               │
│   │  TTS Engine  │────────────┤                      │               │
│   │  (Edge TTS)  │  voice.mp3 │                      │               │
│   │              │  boundaries│                      │               │
│   └──────┬───────┘            │                      │               │
│          │                    │                      │               │
│          ▼                    │                      │               │
│   ┌──────────────┐            │                      │               │
│   │  Segmenter   │            │                      │               │
│   │ (line-split) │            │                      │               │
│   └──────┬───────┘            │                      │               │
│          │                    │                      │               │
│          ▼                    │                      │               │
│   ┌──────────────┐            │                      │               │
│   │     ASS      │────────────┘                      │               │
│   │  Generator   │  subs.ass                         │               │
│   └──────┬───────┘                                   │               │
│          │                                           │               │
│          ▼                                           │               │
│   ┌──────────────┐                                   │               │
│   │   Karaoke    │───────────────────────────────────┘               │
│   │   Renderer   │                                                   │
│   │   (FFmpeg)   │                                                   │
│   └──────────────┘                                                   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. Text Normalizer (`normalizer.py`)

**Purpose**: Prepare input text for consistent TTS synthesis.

```python
@dataclass
class NormalizationConfig:
    collapse_whitespace: bool = True
    normalize_quotes: bool = True      # Convert fancy quotes to standard
    normalize_dashes: bool = True      # Convert em/en dashes to hyphen
    strip_control_chars: bool = True   # Remove non-printable chars
    number_format: str = "spoken"      # "spoken" | "digits"

class TextNormalizer:
    def __init__(self, config: NormalizationConfig = None):
        self.config = config or NormalizationConfig()
    
    def normalize(self, text: str) -> str:
        """Normalize text for TTS synthesis."""
        
    def tokenize(self, text: str) -> List[Token]:
        """Split text into word and punctuation tokens."""
```

**Token Types**:
- `WORD`: Text that should be spoken and highlighted
- `PUNCTUATION`: Displayed but not highlighted
- `WHITESPACE`: Not displayed in subtitles

---

### 2. TTS Engine (`tts_engine.py`)

**Purpose**: Synthesize speech and capture word-boundary timings.

```python
@dataclass
class WordBoundary:
    text: str
    audio_offset_ms: int    # Start time in milliseconds
    duration_ms: int        # Duration in milliseconds
    
@dataclass
class TTSResult:
    audio_path: Path
    word_boundaries: List[WordBoundary]
    total_duration_ms: int

class TTSEngine:
    def __init__(
        self,
        language: str = "es-ES",
        voice: str = "es-ES-ElviraNeural",
        rate: str = "+0%",
        volume: str = "+0%"
    ):
        pass
        
    async def synthesize(
        self, 
        text: str, 
        output_path: Path
    ) -> TTSResult:
        """Synthesize speech with word-boundary capture."""
```

**Edge TTS Integration**:
- Uses `edge_tts.Communicate` for synthesis
- Subscribes to `WordBoundary` events for timing data
- Stores `audioOffset` (100-nanosecond units) and `duration` per word

**Timing Interpolation**:
If some words lack timing data:
1. Calculate average word duration from available data
2. Distribute missing words proportionally between known boundaries
3. Log warning with percentage of interpolated words

---

### 3. Subtitle Segmenter (`segmenter.py`)

**Purpose**: Split word stream into subtitle events (one line per event).

```python
@dataclass
class SegmentationConfig:
    max_chars_per_line: int = 40      # Maximum characters per subtitle line
    min_words_per_segment: int = 2    # Minimum words before line break
    max_words_per_segment: int = 8    # Maximum words per segment

@dataclass
class SubtitleEvent:
    start_time_ms: int
    end_time_ms: int
    words: List[WordBoundary]

class SubtitleSegmenter:
    def __init__(self, config: SegmentationConfig = None):
        self.config = config or SegmentationConfig()
        
    def segment(
        self, 
        word_boundaries: List[WordBoundary]
    ) -> List[SubtitleEvent]:
        """Segment words into subtitle events for single-line display."""
```

**Segmentation Rules**:
1. Never exceed `max_chars_per_line` characters per line
2. Prefer breaking at punctuation (comma, period)
3. If no punctuation, break at `max_words_per_segment`
4. Each segment starts when previous ends (no overlap)

---

### 4. ASS Generator (`ass_generator.py`)

**Purpose**: Generate ASS subtitle file with pink box highlights and bold uppercase text.

```python
@dataclass
class SubtitleStyle:
    font_name: str = "Arial Bold"
    font_size: int = 100
    primary_color: str = "&H00FFFFFF"    # White (text color)
    secondary_color: str = "&H005500FF"  # Pink (active highlight color)
    outline_color: str = "&H00000000"    # Black outline (always visible)
    back_color: str = "&H005500FF"       # Pink box background
    outline_width: float = 3.0           # Black border thickness
    shadow_depth: float = 0.0            # No shadow
    alignment: int = 2                    # Bottom center
    margin_v: int = 300                   # Centered relative to screen composition
    margin_l: int = 60
    margin_r: int = 60
    use_uppercase: bool = True           # All text must be UPPERCASE

**Visual Requirements**:
- **Font**: Impactful, high-readability sans-serif (Arial Bold or similar).
- **Colors**: Solid Pink (Magenta `#FF0055`) for the highlight box, Pure White (`#FFFFFF`) for text.
- **Dynamic Style**: 
    - **Inactive words**: White text with a 3px black outline (to be visible on any background).
    - **Active word**: White text inside a solid pink box (no outline/shadow).
- **Normalization**: All subtitle text must be converted to UPPERCASE for maximum impact.

class ASSGenerator:
    def __init__(self, style: SubtitleStyle = None):
        self.style = style or SubtitleStyle()
        
    def generate(
        self,
        events: List[SubtitleEvent],
        output_path: Path,
        video_width: int = 1080,
        video_height: int = 1920
    ) -> Path:
        """Generate ASS file with karaoke tags."""
```

**ASS Karaoke Format**:
```
Dialogue: 0,0:00:00.00,0:00:02.50,Default,,0,0,0,,{\kf80}Hello {\kf60}world {\kf100}everyone
```

- `\kf` = karaoke fill effect (progressive highlight)
- Duration in centiseconds (100ths of a second)
- Punctuation gets `{\kf0}` (zero duration, no highlight)

---

### 5. Karaoke Renderer (`renderer.py`)

**Purpose**: Assemble final video with audio and burned-in subtitles.

> [!NOTE]
> While this component is currently part of the subtitles module, it implements generic video processing logic (cropping, looping, merging) that could be moved to a top-level `src/video/` utility in the future.

```python
@dataclass
class RendererConfig:
    target_width: int = 1080
    target_height: int = 1920
    fps: int = 30
    video_codec: str = "libx264"
    audio_codec: str = "aac"
    crf: int = 23                     # Quality (lower = better)
    preset: str = "medium"

class KaraokeRenderer:
    def __init__(self, config: RendererConfig = None):
        self.config = config or RendererConfig()
        
    def render_video(
        self,
        background_video: Path,
        audio: Path,
        subtitles: Path,
        output: Path,
        target_duration_ms: int
    ) -> Path:
        """Compose final video with audio and burned-in subtitles."""
```

**Video Processing Pipeline**:
1. **Probe** background video for duration and dimensions
2. **Crop** to 9:16 if aspect ratio differs (center crop)
3. **Loop/Trim** to match audio duration:
   - If shorter: loop video (`-stream_loop -1`)
   - If longer: trim to audio length
4. **Burn subtitles** using `subtitles` filter (libass)
5. **Mix audio** track with video
6. **Encode** to final output

**FFmpeg Command Structure**:
```bash
ffmpeg -stream_loop -1 -i bg.mp4 -i voice.mp3 \
  -vf "crop=ih*9/16:ih,scale=1080:1920,subtitles=subs.ass" \
  -c:v libx264 -c:a aac -shortest \
  -t {audio_duration} final.mp4
```

---

### 6. Storage Manager (`storage.py`)

**Purpose**: Manage artifact storage with content-based hashing.

```python
class StorageManager:
    def __init__(self, base_dir: Path = Path("data/audio")):
        self.base_dir = base_dir
        
    def get_content_hash(self, text: str) -> str:
        """Generate SHA-256 hash (first 12 chars) of normalized text."""
        
    def get_artifact_dir(self, text: str) -> Path:
        """Get or create directory for text artifacts."""
        
    def save_metadata(
        self, 
        artifact_dir: Path, 
        config: dict,
        stats: dict
    ) -> Path:
        """Save generation metadata for reproducibility."""
```

**Directory Structure**:
```
data/audio/
└── a1b2c3d4e5f6/          # First 12 chars of SHA-256
    ├── voice.mp3          # Synthesized audio
    ├── word_boundaries.json
    ├── subs.ass
    └── metadata.json      # Generation config + stats
```

---

### 7. Main Pipeline (`pipeline.py`)

**Purpose**: Orchestrate the complete generation process.

```python
@dataclass
class KaraokeConfig:
    language: str = "es-ES"
    voice: str = "es-ES-ElviraNeural"
    normalization: NormalizationConfig = field(default_factory=NormalizationConfig)
    segmentation: SegmentationConfig = field(default_factory=SegmentationConfig)
    style: SubtitleStyle = field(default_factory=SubtitleStyle)
    renderer: RendererConfig = field(default_factory=RendererConfig)

@dataclass
class KaraokeResult:
    success: bool
    output_path: Optional[Path]
    artifact_dir: Path
    audio_duration_ms: int
    word_count: int
    segment_count: int
    interpolated_words_pct: float
    error: Optional[str] = None

class KaraokePipeline:
    def __init__(self, config: KaraokeConfig = None):
        self.config = config or KaraokeConfig()
        
    async def create(
        self,
        script_path: Path,
        background_video: Path,
        output_path: Path
    ) -> KaraokeResult:
        """Execute full pipeline: text → TTS → ASS → video."""
```

**Pipeline Steps**:
1. Read and normalize script text
2. Check/create artifact directory based on text hash
3. Synthesize TTS with word boundaries (or reuse cached)
4. Segment words into subtitle events
5. Generate ASS file with karaoke tags
6. Render final video using KaraokeRenderer
7. Save metadata and return result

---

## Decisions

### D1: Content-Based Artifact Hashing
**Decision**: Use SHA-256 hash of normalized text for artifact directory naming.
**Rationale**: 
- Enables caching: same text = same audio (no re-synthesis)
- Collision-resistant for practical purposes
- 12 characters provide 48 bits of uniqueness

### D2: ASS Format for Subtitles
**Decision**: Use ASS (Advanced SubStation Alpha) format exclusively.
**Rationale**:
- Native karaoke tag support (`\k`, `\kf`, `\ko`)
- Rich styling capabilities
- Excellent FFmpeg/libass support
- Industry-proven for karaoke applications

### D3: Edge TTS for Speech Synthesis
**Decision**: Use Edge TTS as the primary TTS engine.
**Rationale**:
- Free tier with high quality
- Word-boundary event support via SSML
- Multi-language support
- No API key required

### D4: Center Crop for Aspect Ratio
**Decision**: Crop background video to 9:16 from center.
**Rationale**:
- Preserves quality (no stretching)
- Center framing usually captures important content
- Simple, predictable behavior

### D5: Independent Module with Specialized Renderer
**Decision**: Create as standalone module. Use `KaraokeRenderer` for video assembly.
**Rationale**:
- `KaraokeRenderer` name specifically describes its purpose within this module.
- Generic video operations (loop, crop) are encapsulated but can be extracted to `src/utils/` if a central video processing utility is developed later.
- Avoids the overly generic "Composer" name.

---

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Edge TTS API changes | Abstract TTS interface; can swap implementations |
| Missing word boundaries | Interpolation fallback with logged warnings |
| FFmpeg not installed | Clear error message with installation instructions |
| Large text files | Add reasonable limits (e.g., 5000 chars) with warning |
| Non-UTF8 encoding | Force UTF-8 encoding on read |

---

## Open Questions

1. **Voice presets**: Should we bundle common voice configurations (e.g., `spanish_female`, `english_male`)?
2. **Progress reporting**: Should CLI show progress bar for long generations?
3. **Preview mode**: Generate subtitle preview without full video encoding?

---

## Future Extensions (Not in Scope)

- **Batch mode**: Process multiple scripts from directory
- **LLM integration**: Generate scripts from prompts
- **Music mixing**: Add background music track
- **Style presets**: Bundled visual themes (neon, minimal, bold)
- **Auto-backgrounds**: Generate video from images via VideoCreator
