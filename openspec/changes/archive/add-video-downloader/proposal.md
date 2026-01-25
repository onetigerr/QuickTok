# Change: Add Video Downloader

## Why
We need an automated way to process Apify JSON datasets, filter high-potential Douyin videos based on engagement and freshness, and download them for manual editing.

## What Changes
- New Python script `src/downloader.py` to parse JSON and download videos.
- Support for filtering by age (max 14 days) and popularity (5k+ likes or Rocket formula).
- Automated directory organization by download date.
- Generate `report.md` in the download folder with video metadata.
- Download video thumbnails to `thumbnails/` subdirectory.

## Impact
- Affected specs: `video-downloader` (New capability)
- Affected code: `src/downloader.py`, `data/` directory.
