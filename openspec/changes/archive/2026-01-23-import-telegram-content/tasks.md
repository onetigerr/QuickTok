# Tasks: Import Telegram Content

## Phase 1: Infrastructure Setup
- [x] 1.1 Add `telethon` to `requirements.txt`
- [x] 1.2 Create directory structure: `src/telegram/`, `src/telegram/adapters/`
- [x] 1.3 Verify session file exists in `data/sessions/`

## Phase 2: Core Models & Database
- [x] 2.1 Create `src/telegram/models.py` with Pydantic models (`ContentFormat`, `NormalizedMetadata`, `ImportedPost`, `ImportResult`)
- [x] 2.2 Create `src/telegram/database.py` with `TelegramImportDB` class (SQLite)
- [x] 2.3 Write unit tests for database operations (`tests/test_telegram_db.py`)

## Phase 3: Adapter System
- [x] 3.1 Create `src/telegram/adapters/base.py` with `BaseAdapter` ABC
- [x] 3.2 Create `src/telegram/adapters/ccumpot.py` with `CCumpotAdapter`
- [x] 3.3 Write unit tests for CCumpotAdapter parsing logic (`tests/test_ccumpot_adapter.py`)

## Phase 4: Telegram Client
- [x] 4.1 Create `src/telegram/client.py` with `TelegramClientWrapper`
- [x] 4.2 Implement `connect()` method
- [x] 4.3 Implement `import_channel()` with pagination logic
- [x] 4.4 Implement `download_media()` method
- [x] 4.5 Implement error handling (3 consecutive errors → stop)

## Phase 5: CLI & Integration
- [x] 5.1 Create `run_import.py` CLI entrypoint
- [x] 5.2 Implement adapter registry
- [x] 5.3 Manual integration test: `python run_import.py --channel CCumpot --limit 5`

## Verification Criteria
- [x] Database correctly tracks imported posts (no duplicates on re-run)
- [x] Media files saved to `data/incoming/{channel}/{timestamp}/`
- [x] 3 consecutive download errors stop the process
- [x] `--limit` parameter correctly limits processed posts
