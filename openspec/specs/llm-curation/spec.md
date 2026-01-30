# llm-curation Specification

## Purpose
TBD - created by archiving change llm-curation-pipeline. Update Purpose after archive.
## Requirements
### Requirement: Thumbnail Optimization
The system MUST optimize images before sending them to the LLM to minimize token usage and latency while maintaining sufficient visual quality for assessment.

#### Scenario: Image resizing
**Given** a high-resolution input image (e.g., 4000x3000)
**When** the `ThumbnailGenerator` processes the image
**Then** the output image dimensions MUST NOT exceed 512x512 pixels
**And** the aspect ratio MUST be preserved

#### Scenario: Image compression
**Given** an input image
**When** the `ThumbnailGenerator` processes the image
**Then** the output file size SHOULD be approximately 30-50KB
**And** the format MUST be JPEG

---

### Requirement: LLM Scoring
The system MUST obtain a structured evaluation score for each image from a vision-capable LLM.

#### Scenario: Successful scoring
**Given** a valid image path
**When** `ImageScorer.score()` is called
**Then** it returns an `ImageScore` object containing `wow_factor`, `engagement`, `tiktok_fit` (integers 1-10) and `is_explicit` (boolean)

#### Scenario: Explicit content detection
**Given** an image containing NSFW content
**When** the LLM evaluates the image
**Then** `is_explicit` MUST be true
**And** the `combined_score` MUST be 0

---

### Requirement: Curation Decision Logic
The system MUST filter images based on a configurable score threshold and move selected images to the curated directory.

#### Scenario: High scoring image
**Given** an image with a combined score of 8.0
**And** the threshold is set to 7.0
**And** `is_explicit` is false
**When** the pipeline processes the image
**Then** the image is copied/moved to `data/curated/{channel}/{timestamp}/`
**And** the selection is logged

#### Scenario: Low scoring image
**Given** an image with a combined score of 5.0
**And** the threshold is set to 7.0
**When** the pipeline processes the image
**Then** the image is NOT moved to `data/curated/`
**And** the rejection is logged

#### Scenario: Dry run mode
**Given** the pipeline is running in `dry_run=True` mode
**And** an image meets the selection criteria
**When** the pipeline processes the image
**Then** the image is NOT moved or copied
**But** the "would be selected" status is reported

---

### Requirement: Batch Processing
The system MUST support processing entire directories of imported content.

#### Scenario: Curating a channel folder
**Given** a folder `data/incoming/ChannelName/Timestamp/` containing 10 images
**When** the curation command is run on this folder
**Then** all 10 images are evaluated
**And** a summary report is generated showing total processed, selected, and rejected counts

