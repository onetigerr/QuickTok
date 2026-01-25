## ADDED Requirements

### Requirement: JSON Parsing
The system SHALL parse Apify Douyin scraper JSON files to extract video ID, creation time, like count, and play URL.

#### Scenario: Successful Parsing
- **WHEN** a valid Apify Douyin JSON is provided
- **THEN** extract `id`, `createTime`, `statistics.diggCount`, and `videoMeta.playUrl`

### Requirement: Velocity Filtering (The Rocket Formula)
The system SHALL identify "Rocket" videos based on age and likes.

#### Scenario: Rocket Video Detection
- **WHEN** a video is 2-3 days old
- **AND** has 3,000+ likes
- **THEN** it MUST be selected for download

### Requirement: Standard Filtering
The system SHALL filter videos based on general freshness and popularity.

#### Scenario: Standard Success
- **WHEN** a video is <= 14 days old (ideally 3-7 days)
- **AND** has 5,000+ likes
- **THEN** it MUST be selected for download

### Requirement: Automated Acquisition
The system SHALL download selected videos to a structured local directory.

#### Scenario: File Organization
- **WHEN** a video is approved for download
- **THEN** save it to `data/YYYY-MM-DD/{video_id}.mp4` where YYYY-MM-DD is the current local date.

### Requirement: Metadata Reporting
The system SHALL generate a markdown report for downloaded videos.

#### Scenario: Report Generation
- **WHEN** videos are downloaded
- **THEN** create `data/YYYY-MM-DD/report.md`
- **AND** include table with: ID, Likes, Age, Duration, Resolution, Thumbnail image.

### Requirement: Thumbnails
The system SHALL download thumbnails for selected videos.

#### Scenario: Thumbnail Storage
- **WHEN** a video is downloaded
- **THEN** download its cover image to `data/YYYY-MM-DD/thumbnails/{video_id}.jpg`
