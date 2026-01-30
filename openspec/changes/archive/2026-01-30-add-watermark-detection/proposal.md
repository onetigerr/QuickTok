# Change: Add Watermark Detection

## Why
Images sourced from external platforms often contain watermarks (text, URLs, or logos) typically located at the bottom. To support future automated filtering or processing, the LLM curation system needs to detect these watermarks and record their position.

## What Changes
- **LLM Scorer**: Update prompt to detect watermarks and calculate vertical offset as a percentage (0-100%).
- **Models**: Add `watermark_offset_pct` field to `ImageScore` Pydantic model.
- **Database**: Add `watermark_offset_pct` column to `photo_scores` table.
- **Pipeline**: Ensure watermark data is passed from LLM response to database storage.

## Impact
- **Affected specs**: `llm-curation`
- **Affected code**: `curation/models.py`, `curation/pipeline.py`, `curation/prompts.py`, `telegram/database.py`, `data/prompts/scoring_system.txt`
