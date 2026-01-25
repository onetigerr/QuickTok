# telegram-client Specification

## Purpose
TBD - created by archiving change import-telegram-content. Update Purpose after archive.
## Requirements
### Requirement: Session-Based Authentication
The client MUST authenticate using pre-existing `.session` files located in `data/sessions/`.

#### Scenario: Valid session file
**Given** a session file exists at `data/sessions/{name}.session`
**When** `TelegramClientWrapper` is initialized with that session name
**Then** it connects to Telegram without prompting for login

#### Scenario: Missing session file
**Given** no session file exists for the specified name
**When** `TelegramClientWrapper` is initialized
**Then** it raises `SessionNotFoundError` with a descriptive message

---

### Requirement: Channel History Iteration
The client MUST iterate through channel history from newest to oldest posts.

#### Scenario: Paginated iteration
**Given** a connected client and a channel with 100 posts
**When** `import_channel()` is called with no limit
**Then** all 100 posts are processed in order from newest to oldest

#### Scenario: Limited iteration
**Given** a connected client and a channel with 100 posts
**When** `import_channel()` is called with `limit=20`
**Then** only the 20 most recent posts are processed

---

### Requirement: Media Download
The client MUST download all media attachments from a message to a timestamped folder.

#### Scenario: Post with multiple photos
**Given** a message with 3 photo attachments
**When** `download_media()` is called
**Then** all 3 photos are saved to `data/incoming/{channel}/{timestamp}/` with original filenames

#### Scenario: Post with video
**Given** a message with 1 video attachment
**When** `download_media()` is called
**Then** the video is saved with its original filename

---

### Requirement: Duplicate Prevention
The client MUST skip posts that already exist in the database.

#### Scenario: Re-running import
**Given** a post with `post_id=123` already in database for channel "CCumpot"
**When** `import_channel()` encounters that post again
**Then** the post is skipped and `skipped_duplicates` counter increments

---

### Requirement: Error Tolerance with Circuit Breaker
The client MUST tolerate individual download failures but stop after 3 consecutive errors.

#### Scenario: Single download failure
**Given** an active import process
**When** one media download fails
**Then** the error is logged, the post is skipped, and import continues

#### Scenario: Circuit breaker triggered
**Given** an active import process
**When** 3 consecutive media downloads fail
**Then** import stops immediately and returns `ImportResult` with `stopped_early=True`

#### Scenario: Error counter reset
**Given** 2 consecutive download failures have occurred
**When** the next download succeeds
**Then** the consecutive error counter resets to 0

