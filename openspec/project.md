# Project: QuickTok

## Overview
QuickTok is a workspace for manual and semi-automated video editing for TikTok. The project focuses on sourcing high-quality video content from multiple platforms (Douyin, Telegram), processing it with AI-assisted curation, and preparing it for manual assembly.

## Core Goals
- **Multi-Source Sourcing**: Automate the collection of videos and images from Douyin (via Apify JSON) and Telegram channels (via Telethon).
- **Content Curation**: Filter Douyin videos based on the "Rocket" formula (high velocity + recent engagement).
- **AI-Powered Selection**: Use LLM-based analysis to sort and select the most suitable media from imported content.
- **Automated Processing**: Download selected high-potential videos locally.
- **Manual Assembly**: Support manual video editing for TikTok.

## Workflows

### Douyin Workflow
1. **Import**: Accept JSON data from `data/incoming.json/` (Apify Douyin Scraper results).
2. **Analysis**: Parse `createTime`, `statistics.diggCount`, and `videoMeta.playUrl`.
3. **Selection (Filtering Rules)**:
    - **Max Age**: 14 days.
    - **Ideal Age**: 3-7 days.
    - **Min Likes**: 5,000 - 10,000.
    - **The "Rocket" Formula**: Age 2-3 days AND Likes > 3,000.
4. **Acquisition**: Download videos to `data/{download_date}/{video_id}.mp4`.

### Telegram Workflow
1. **Import**: Connect to Telegram channel via Telethon session.
2. **Scraping**: Iterate through channel history (newest to oldest), download media.
3. **Normalization**: Extract metadata (model name, set name) via channel-specific adapters.
4. **Storage**: Save media to `data/incoming/{channel}/{timestamp}/`, metadata to SQLite.
5. **Deduplication**: Skip posts already in database (by channel + post_id).

### LLM Curation
1. **Input**: Media files from `data/incoming/` with metadata.
2. **Analysis**: LLM evaluates visual quality, relevance, and suitability for TikTok.
3. **Scoring**: Each item receives a score/ranking.
4. **Selection**: Top-ranked items moved to `data/curated/` for manual assembly.

## Tech Stack
- **Language**: Python 3.10+
- **Data Management**: Pydantic for data validation and schema definition.
- **Video Downloading**: `yt-dlp` for extracting and downloading video streams.
- **Telegram Integration**: Telethon for API access and media download.
- **Video Processing**: FFmpeg (via `ffmpeg-python`) for editing tasks.
- **LLM Integration**: Groq/OpenAI for AI-powered content analysis.
- **CLI**: `typer` or `click` for command-line interfaces.
- **Project Structure**: Modern Python structure with `pyproject.toml` and `src/`.

## Project Conventions
- **Specifications**: Follow the OpenSpec format in `openspec/`.
- **Directory Structure**:
    - `data/temp/`: Temporary storage for Apify JSON imports.
    - `data/incoming/`: Raw imported content (Telegram channels, etc.).
    - `data/raw/`: Original downloaded videos and their metadata.
    - `data/curated/`: LLM-selected content for manual assembly.
    - `data/processed/`: Videos after initial processing (trimming, etc.).
    - `data/sessions/`: Telegram session files.
    - `src/`: Core Python source code.
    - `openspec/`: Project documentation and requirement specs.
- **Coding Style**: Follow PEP 8. Use type hints extensively.
- **Error Handling**: Use custom exceptions and logging instead of raw prints.
