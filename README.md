# QuickTok

QuickTok is a workspace for manual and semi-automated video editing for TikTok. It sources high-quality video content from multiple platforms (Douyin, Telegram), processes it with AI-assisted curation, and prepares it for manual assembly.

## Core Features

- **Multi-Source Sourcing**: Automate collection from Douyin (Apify) and Telegram (Telethon).
- **AI-Powered Curation**: Use LLM-based analysis to score and select the best media.
- **Karaoke Subtitles**: Generate TikTok-ready videos with synchronized TTS audio and karaoke-style subtitles.
- **Automated Processing**: Download and organize high-potential videos.
- **Manual Assembly**: Support for final manual video editing.

## Setup

1.  **Clone the repository**.
2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
3.  **Environment Variables**:
    Create a `.env` file in the root directory with the following:
    ```env
    TELEGRAM_API_ID=your_api_id
    TELEGRAM_API_HASH=your_api_hash
    GROQ_API_KEY=your_groq_api_key
    ```
4.  **Session Files**:
    Place your Telegram `.session` files in `data/sessions/`.

## Usage

### Telegram Import

To import content from a Telegram channel, use the `src.importer` module. The importer connects via your session file, downloads media (images/videos) from posts and comments, extracts metadata, and saves everything to `data/incoming/`.

**Command:**

```bash
python -m src.importer --channel <CHANNEL_NAME> [--limit <N>]
```

**Arguments:**

*   `--channel`: (Required) The name of the channel adapter to use (e.g., `ccumpot`).
*   `--limit`: (Optional) The number of **new** posts to process. If omitted, it processes the entire history (or until stopped).

**Example:**

```bash
# Import the last 10 new posts from the 'ccumpot' channel
python -m src.importer --channel ccumpot --limit 10
```

### LLM Curation

After importing content, use the `src.curation` module to automatically score images and filter out low-quality or explicit content. High-scoring images are copied to `data/curated/` and organized by **Model Name**.

**Commands:**

```bash
# Curate a specific post folder
python -m src.curation curate <PATH_TO_FOLDER>

# Curate all folders in data/incoming/
python -m src.curation curate-all
```

**Options:**

*   `--threshold` (or `-t`): Minimum score (1-10) to select an image (default: `7.0`).
*   `--dry-run` (or `-n`): Simulate the process without moving any files.

**Optimization:**
The module automatically skips folders that have already been processed or already exist in the `data/curated/` directory to save time and API tokens.

### Karaoke Subtitles

Generate videos with synchronized text-to-speech audio and karaoke-style subtitles for TikTok. See detailed documentation in [`src/subtitles/README.md`](src/subtitles/README.md).

**Quick Example:**

```bash
python -m src.subtitles \
  --script script.txt \
  --bg background.mp4 \
  --output final.mp4 \
  --lang es-ES
```

**Features:**
- Word-accurate karaoke highlighting
- Multi-language TTS support (Edge TTS)
- Automatic 9:16 aspect ratio cropping
- Customizable subtitle styles
- Artifact caching for fast regeneration


## Project Structure

- `src/`: Core source code.
    - `src/importer`: Module for executing imports.
    - `src/curation`: LLM-based image scoring and filtering.
    - `src/subtitles`: Karaoke subtitles generation with TTS.
    - `src/telegram`: Telegram client and database logic.
- `data/`: Data storage (incoming, curated, audio, sessions, etc.).
- `openspec/`: Project specifications and documentation.
