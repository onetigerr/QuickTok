# content-adapter Specification

## Purpose
TBD - created by archiving change import-telegram-content. Update Purpose after archive.
## Requirements
### Requirement: Abstract Adapter Interface
All adapters MUST implement `BaseAdapter` with standardized methods.

#### Scenario: Adapter interface compliance
**Given** a class inheriting from `BaseAdapter`
**When** it does not implement `channel_name`, `filter()`, or `extract_metadata()`
**Then** instantiation raises `TypeError`

---

### Requirement: Post Filtering
Adapters MUST provide a `filter(message)` method to determine if a post should be downloaded.

#### Scenario: CCumpot - Post with media
**Given** a Telegram message with photo or video attachment
**When** `CCumpotAdapter.filter()` is called
**Then** it returns `True`

#### Scenario: CCumpot - Text-only post
**Given** a Telegram message without any media
**When** `CCumpotAdapter.filter()` is called
**Then** it returns `False`

---

### Requirement: Metadata Extraction
Adapters MUST extract structured metadata from message content.

#### Scenario: CCumpot - Standard format
**Given** a message with caption:
```
Контент модели🦄
💕Annfigma💕
Принес еще один новогодний сетик🔥
```
**When** `CCumpotAdapter.extract_metadata()` is called
**Then** it returns `model_name="Annfigma"` (second line, emoji stripped) and `set_name="Принес еще один новогодний сетик"` (third line, emoji stripped)

#### Scenario: CCumpot - Only two lines
**Given** a message with caption containing only two lines
**When** `CCumpotAdapter.extract_metadata()` is called
**Then** `model_name` is extracted from second line and `set_name` is `None`

#### Scenario: CCumpot - Single line caption
**Given** a message with only one line of text
**When** `CCumpotAdapter.extract_metadata()` is called
**Then** `model_name` is "Unknown" and `set_name` is `None`

#### Scenario: CCumpot - Empty caption
**Given** a message with no caption/text
**When** `CCumpotAdapter.extract_metadata()` is called
**Then** `model_name` is "Unknown" and `set_name` is `None`

---

### Requirement: Content Format Detection
Adapters MUST correctly identify content format based on attachments.

#### Scenario: Photo-only post
**Given** a message with only photo attachments
**When** content format is detected
**Then** `content_format` is `ContentFormat.PHOTO`

#### Scenario: Video-only post
**Given** a message with only video attachments
**When** content format is detected
**Then** `content_format` is `ContentFormat.VIDEO`

#### Scenario: Mixed content post
**Given** a message with both photo and video attachments
**When** content format is detected
**Then** `content_format` is `ContentFormat.MIXED`

---

### Requirement: Comment Media Extraction
Adapters MUST download media from both the main post and its comments.

#### Scenario: Post with comment images
**Given** a Telegram post with images in comments
**When** the post is processed
**Then** all images from the main post AND all images from comments are downloaded to the same folder

#### Scenario: Comment without media
**Given** a comment without any media attachments
**When** iterating through comments
**Then** the comment is skipped without error

---

### Requirement: Limit Behavior
The `--limit` parameter MUST specify the number of NEW posts to download, not the total number of posts to check.

#### Scenario: Limit with duplicates
**Given** a channel with 10 posts where the first 3 are duplicates
**When** importing with `--limit=5`
**Then** the system processes posts 1-8 (skipping 3 duplicates) and downloads exactly 5 new posts

#### Scenario: Limit reached
**Given** importing with `--limit=5`
**When** 5 new posts have been downloaded
**Then** the import stops even if there are more posts in the channel

---

### Requirement: Adapter Registry
The system MUST support registering multiple adapters and selecting by channel name.

#### Scenario: Known channel
**Given** an adapter registry with `CCumpotAdapter` registered
**When** looking up adapter for "ccumpot" (case-insensitive)
**Then** returns the `CCumpotAdapter` instance

#### Scenario: Unknown channel
**Given** an adapter registry
**When** looking up adapter for an unregistered channel
**Then** returns `None` or raises `UnknownChannelError`

