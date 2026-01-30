# Tasks: Add Watermark Detection

## 1. Preparation
- [x] 1.1 Verify current database state
- [x] 1.2 Identify all locations requiring `ImageScore` updates

## 2. Model & Database Updates
- [x] 2.1 Update `ImageScore` in `src/curation/models.py`
- [x] 2.2 Update `photo_scores` table schema in `src/telegram/database.py`
- [x] 2.3 Update `save_photo_score` method to handle the new field

## 3. LLM Interaction
- [x] 3.1 Update `data/prompts/scoring_system.txt` with new instructions
- [x] 3.2 Update `ImageScorer.score_batch` to handle the expanded JSON (implicitly handled by Pydantic)

## 4. Pipeline Integration
- [x] 4.1 Update `CurationPipeline` to pass the field correctly
- [x] 4.2 Validate data flow from LLM to DB

## 5. Verification
- [x] 5.1 Add unit tests for the updated model
- [x] 5.2 Add integration tests for DB persistence
- [x] 5.3 Verify prompt performance with sample images
