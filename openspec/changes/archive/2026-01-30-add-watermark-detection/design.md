# Design: Watermark Detection

## Context
The system currently scores images but ignores watermarks. We need to capture watermark location for future use.

## Technical Decisions
- **Data Type**: Use `REAL` in SQLite to store the percentage.
- **Measurement**: All offsets are measured from the **Top** of the image (0%) to the **Bottom** (100%).
- **Validation**: Pydantic `Field` validation will ensure the value is between 0 and 100 or null.

## Database Migration
A manual column addition is required for existing installations:
```sql
ALTER TABLE photo_scores ADD COLUMN watermark_offset_pct REAL;
```
The `TelegramImportDB` class will be updated to handle this column during initialization if it doesn't exist.

## Pipeline Flow
1. `ImageScorer` receives images and sends them to Groq.
2. Groq returns JSON including `watermark_offset_pct`.
3. `CurationPipeline` maps the LLM response to `ImageScore` model.
4. `TelegramImportDB` saves the score including the new field.
