# Capability: Subtitles

## ADDED Requirements

### Requirement: Text Normalization

The system SHALL normalize input text before TTS synthesis to ensure consistent pronunciation and timing.

Normalization MUST include:
- Collapsing multiple whitespace characters to single space
- Converting fancy quotes (", ", ', ') to standard ASCII quotes
- Converting em/en dashes to standard hyphens
- Removing non-printable control characters
- Preserving UTF-8 encoded text

The system SHALL tokenize text into distinct word and punctuation tokens for separate handling during subtitle generation.

#### Scenario: Normalize text with fancy characters
- **WHEN** input text contains smart quotes and em dashes
- **THEN** they are converted to ASCII equivalents
- **AND** normalized text is used for TTS synthesis

#### Scenario: Tokenize mixed text
- **WHEN** input is "Hello, world!"
- **THEN** tokens are: WORD("Hello"), PUNCT(","), WORD("world"), PUNCT("!")

---

### Requirement: TTS Synthesis with Word Boundaries

The system SHALL synthesize speech from normalized text using Edge TTS and capture word-boundary timing events.

For each word, the system SHALL capture:
- `audioOffset`: Start time in the audio stream
- `duration`: Duration of the word pronunciation

The system SHALL store synthesized audio as an MP3 file and word boundaries as JSON.

#### Scenario: Synthesize Spanish text
- **WHEN** text "Hola mundo" is synthesized with voice "es-ES-ElviraNeural"
- **THEN** audio file is created
- **AND** word boundaries contain timing for "Hola" and "mundo"

#### Scenario: Missing word boundaries
- **WHEN** TTS engine does not return timing for some words
- **THEN** system SHALL interpolate missing timings based on average word duration
- **AND** log a warning with percentage of interpolated words

---

### Requirement: Multi-Language Support

The system SHALL support configurable language and voice selection for TTS synthesis.

Default configuration:
- Language: `es-ES` (Spanish - Spain)
- Voice: `es-ES-ElviraNeural`

The system SHALL accept any valid Edge TTS language code and voice name.

#### Scenario: Use different language
- **WHEN** user specifies `--lang en-US --voice en-US-JennyNeural`
- **THEN** TTS uses English voice for synthesis

---

### Requirement: Single-Line Subtitle Segmentation

The system SHALL segment word stream into subtitle events where each event displays as a single line on screen.

Segmentation rules:
- Maximum characters per line: configurable (default 40)
- Never wrap to two lines; create new event instead
- Prefer breaking at punctuation marks
- Minimum 2 words per segment (unless constrained by length)

Each subtitle event SHALL have start time (first word start) and end time (last word end).

#### Scenario: Segment long sentence
- **WHEN** sentence is "Esta es una oración muy larga que no cabe en una línea"
- **THEN** multiple subtitle events are created
- **AND** each event fits within max character limit
- **AND** events are displayed sequentially with no overlap

---

### Requirement: ASS Karaoke Subtitle Generation

The system SHALL generate ASS (Advanced SubStation Alpha) format subtitles with karaoke fill effects.

Each word SHALL be prefixed with `\kf` tag containing duration in centiseconds (100ths of second).

Punctuation marks SHALL be displayed but NOT highlighted (zero duration or separate non-karaoke span).

#### Scenario: Generate karaoke line
- **WHEN** subtitle event contains words "Hola" (500ms) and "mundo" (600ms)
- **THEN** ASS dialogue line contains `{\kf50}Hola {\kf60}mundo`

#### Scenario: Handle punctuation
- **WHEN** subtitle event is "Hello, world!"
- **THEN** comma and exclamation are displayed
- **AND** they receive zero karaoke duration
- **AND** only "Hello" and "world" are highlighted

---

### Requirement: Customizable Subtitle Styling

The system SHALL support customizable subtitle appearance through configuration.

Configurable properties:
- Font name and size
- Primary color (unhighlighted text)
- Secondary color (highlighted/karaoke fill)
- Outline color and width
- Background/shadow settings
- Vertical alignment (top, center, bottom)
- Margins (left, right, vertical)

Default style: White text with yellow karaoke highlight, black outline, positioned in bottom third.

#### Scenario: Apply custom style
- **WHEN** user provides style configuration JSON
- **THEN** subtitles use specified colors, font, and positioning

#### Scenario: Use default style
- **WHEN** no style configuration is provided
- **THEN** subtitles use default white/yellow karaoke style in bottom third

---

### Requirement: Video Aspect Ratio Enforcement

The system SHALL ensure background video conforms to 9:16 vertical aspect ratio.

If input video has different aspect ratio:
- System SHALL crop (not resize) to 9:16
- Cropping SHALL be center-aligned
- Original resolution quality SHALL be preserved

#### Scenario: Crop horizontal video
- **WHEN** background video is 1920x1080 (16:9)
- **THEN** video is center-cropped to 607.5x1080 equivalent
- **AND** scaled to 1080x1920 output

#### Scenario: Use correct aspect ratio
- **WHEN** background video is already 1080x1920 (9:16)
- **THEN** no cropping is applied

---

### Requirement: Video Duration Alignment

The system SHALL align background video duration to match synthesized audio duration.

Duration policy:
- Audio duration is the source of truth for final video length
- If background is shorter: loop video until audio ends
- If background is longer: trim video to audio length

#### Scenario: Loop short background
- **WHEN** audio is 15 seconds and background is 5 seconds
- **THEN** background is looped 3 times
- **AND** final video is exactly 15 seconds

#### Scenario: Trim long background
- **WHEN** audio is 10 seconds and background is 60 seconds
- **THEN** background is trimmed to first 10 seconds

---

### Requirement: Burned-In Subtitles

The system SHALL burn (render) subtitles directly into video frames rather than as separate subtitle track.

Burned subtitles ensure:
- Universal playback compatibility across all platforms
- Karaoke effects are visible in all players
- No dependency on player subtitle rendering

#### Scenario: Burn subtitles
- **WHEN** video is rendered with ASS subtitles
- **THEN** subtitles are rendered into video frames via FFmpeg libass
- **AND** output video has no separate subtitle track

---

### Requirement: Artifact Storage

The system SHALL store TTS artifacts in organized directory structure using content-based hashing.

Storage structure:
```
data/audio/{content_hash}/
├── voice.mp3
├── word_boundaries.json
├── subs.ass
└── metadata.json
```

Content hash:
- SHA-256 hash of normalized input text
- First 12 characters used for directory name

Metadata SHALL include:
- Generation timestamp
- Language and voice settings
- Normalization config
- Statistics (duration, word count, etc.)

#### Scenario: Store artifacts
- **WHEN** TTS synthesis completes for text
- **THEN** artifacts are saved to `data/audio/{hash}/`
- **AND** metadata.json contains generation parameters

#### Scenario: Reuse cached audio
- **WHEN** same text is processed again
- **THEN** existing audio is reused without re-synthesis
- **AND** log indicates cache hit

---

### Requirement: CLI Interface

The system SHALL provide CLI interface via `python -m src.subtitles`.

Required command: `create`
```
python -m src.subtitles \
  --script <path>    # Input text file (required)
  --bg <path>        # Background video (required)
  --output <path>    # Output video (optional, default: output.mp4)
  --lang <code>      # TTS language (optional, default: es-ES)
  --voice <name>     # TTS voice (optional, default: auto from lang)
  --style-config <path>  # Style JSON (optional)
```

#### Scenario: Create video with defaults
- **WHEN** `python -m src.subtitles --script text.txt --bg video.mp4`
- **THEN** video is created with Spanish TTS and default style
- **AND** output saved to `output.mp4`

#### Scenario: Create video with custom settings
- **WHEN** user specifies `--lang en-US --voice en-US-GuyNeural --style-config style.json`
- **THEN** English voice is used
- **AND** custom style is applied

---

### Requirement: Pipeline Logging

The system SHALL log key metrics during pipeline execution.

Required metrics:
- Audio duration (seconds)
- Background video original duration
- Word count (total)
- Segment count (subtitle events)
- Interpolated words percentage
- Processing time per stage

Logs SHALL use structured logging with clear stage indicators.

#### Scenario: Log pipeline metrics
- **WHEN** pipeline completes successfully
- **THEN** log includes all required metrics
- **AND** final log entry indicates success with output path

#### Scenario: Log warnings
- **WHEN** word boundary interpolation is needed
- **THEN** warning is logged with affected word count and percentage
