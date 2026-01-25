## 1. Implementation
- [ ] 1.1 Define Pydantic models for Douyin metadata in `src/models/douyin.py`.
- [ ] 1.2 Implement `DouyinProcessor` in `src/processors/douyin_processor.py` to parse JSON and filter videos.
- [ ] 1.3 Create CLI command `import-douyin` in `src/cli/import_cmd.py`.
- [ ] 1.4 Add unit tests for parsing and filtering.

## 2. Validation
- [ ] 2.1 Verify import with `data/temp/dataset_douyin-scraper_2026-01-02_10-24-41-422.json`.
- [ ] 2.2 Confirm filtered output is saved to `data/raw/` in a structured format.
