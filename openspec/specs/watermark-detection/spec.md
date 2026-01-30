# watermark-detection Specification

## Purpose
TBD - created by archiving change add-watermark-detection. Update Purpose after archive.
## Requirements
### Requirement: MUST Detect Watermark Presence and Location

The LLM scoring system MUST analyze images for watermarks and report their vertical position.

#### Scenario: Image with watermark at bottom
- **WHEN** the image contains a text or URL watermark at the bottom
- **THEN** it MUST return `watermark_offset_pct` as a float between 0-100 (e.g., 90.50)
- **AND** the offset MUST represent the vertical position from the top of the image

#### Scenario: Image without watermark
- **WHEN** the image contains no visible watermark
- **THEN** it MUST return `watermark_offset_pct` as `null`

#### Scenario: Accuracy precision
- **WHEN** reporting the watermark offset
- **THEN** it MUST use 2 decimal places precision

---

### Requirement: MUST Store Watermark Data

The database MUST persist watermark detection results alongside photo scores.

#### Scenario: Save photo score with watermark
- **WHEN** saving an `ImageScore` with a watermark offset
- **THEN** the value MUST be stored in the `watermark_offset_pct` column of the `photo_scores` table

#### Scenario: Null handling for clean images
- **WHEN** saving an `ImageScore` with no watermark (`null`)
- **THEN** the database column MUST store NULL

---

### Requirement: MUST Update Scoring Prompt

The LLM system prompt MUST include instructions for watermark detection.

#### Scenario: Prompt schema update
- **WHEN** the prompt is sent to the LLM
- **THEN** the JSON output schema MUST include the `watermark_offset_pct` field
- **AND** instructions MUST specify measurement from top (0%) to bottom (100%)

