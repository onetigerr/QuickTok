# Change: Import and Process Douyin Data

## Why
We need a way to ingest raw data from Apify's Douyin Scraper to start selecting and downloading videos. This is the first step in the QuickTok workflow.

## What Changes
- Create a data processing module to parse Douyin Scraper JSON files.
- Define Pydantic models for Douyin video metadata.
- Implement a CLI command to import and filter videos based on statistics (e.g., likes > 1000).

## Impact
- **New Capability**: `douyin-import`
- **Files**:
    - `src/models/douyin.py`: Data models.
    - `src/processors/douyin_processor.py`: Logic for parsing and filtering.
    - `src/cli/import_cmd.py`: CLI interface.
