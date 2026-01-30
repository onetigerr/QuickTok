import json
import logging
import os
import argparse
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional
import requests
from dateutil import parser

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@dataclass
class Video:
    id: str
    create_time: int
    digg_count: int
    play_url: str
    description: str
    cover_url: str
    duration: int  # ms
    width: int
    height: int

class VideoDownloader:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.today = datetime.now(timezone.utc)
        
    def parse_json(self, file_path: str) -> List[Video]:
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return []
            
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            videos = []
            for item in data:
                try:
                    vid_id = item.get('id')
                    create_time = item.get('createTime')
                    
                    # Handle flat keys with dots vs nested dicts for statistics
                    digg_count = item.get('statistics.diggCount')
                    if digg_count is None and 'statistics' in item:
                         digg_count = item['statistics'].get('diggCount')

                    # Handle flat keys vs nested dicts for videoMeta
                    video_meta = item.get('videoMeta', {})
                    # If videoMeta was flat keys in source (unlikely for object fields but possible in some exports)
                    # We prioritize the object structure as seen in user samples
                    
                    play_url = item.get('videoMeta.playUrl')
                    if not play_url:
                        play_url = video_meta.get('playUrl')
                        
                    cover_url = item.get('videoMeta.cover')
                    if not cover_url:
                        cover_url = video_meta.get('cover')
                        
                    duration = item.get('videoMeta.duration')
                    if not duration:
                        duration = video_meta.get('duration', 0)
                        
                    width = item.get('videoMeta.width')
                    if not width:
                        width = video_meta.get('width', 0)
                        
                    height = item.get('videoMeta.height')
                    if not height:
                        height = video_meta.get('height', 0)
                            
                    description = item.get('text', '')

                    if vid_id and create_time and digg_count is not None and play_url:
                        videos.append(Video(
                            id=str(vid_id),
                            create_time=int(create_time),
                            digg_count=int(digg_count),
                            play_url=play_url,
                            description=description,
                            cover_url=cover_url or "",
                            duration=int(duration),
                            width=int(width),
                            height=int(height)
                        ))
                except Exception as e:
                    logger.warning(f"Failed to parse video item: {e}")
                    continue
            
            logger.info(f"Parsed {len(videos)} videos from {file_path}")
            return videos
            
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in {file_path}")
            return []

    def filter_videos(self, videos: List[Video]) -> List[Video]:
        selected_videos = []
        for video in videos:
            # Douyin createTime is typically unix timestamp in seconds
            created_dt = datetime.fromtimestamp(video.create_time, tz=timezone.utc)
            age = self.today - created_dt
            days_old = age.days
            
            is_rocket = False
            is_good = False
            
            # Logic 1: The "Rocket" Formula (Age 2-3 days AND Likes > 3,000)
            # Interpreting "2-3 days ago" as >= 2 days and <= 3 days. 
            if 2 <= days_old <= 3 and video.digg_count > 3000:
                is_rocket = True
                
            # Logic 2: Standard Filtering (Max 14 days, Optimal 3-7 days, Likes 5000-10000+)
            # The prompt says: Max 14 days. Ideal 3-7. Likes > 5000.
            # "Min Likes: 5,000 - 10,000" -> I will treat this as Min Likes >= 5000 for now.
            if days_old <= 14 and video.digg_count >= 5000:
                is_good = True
                
            if is_rocket:
                logger.info(f"🚀 ROCKET DETECTED! Video {video.id}: {days_old} days old, {video.digg_count} likes.")
                selected_videos.append(video)
            elif is_good:
                logger.info(f"✅ Good Candidate: Video {video.id}: {days_old} days old, {video.digg_count} likes.")
                selected_videos.append(video)
            else:
                # Debug log for rejected videos?
                pass
                
        return selected_videos

    def download_video(self, video: Video) -> bool:
        date_str = self.today.strftime('%Y-%m-%d')
        save_dir = os.path.join(self.output_dir, date_str)
        os.makedirs(save_dir, exist_ok=True)
        
        filename = f"{video.id}.mp4"
        file_path = os.path.join(save_dir, filename)
        
        if os.path.exists(file_path):
            logger.info(f"Skipping existing file: {file_path}")
            return True
            
        logger.info(f"Downloading {video.id} to {file_path}...")
        try:
            # Use headers to mimic browser to avoid 403s potentially
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(video.play_url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Successfully downloaded {video.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to download {video.id}: {e}")
            if os.path.exists(file_path):
                os.remove(file_path) # cleanup partial
            return False

    def download_thumbnail(self, video: Video) -> bool:
        date_str = self.today.strftime('%Y-%m-%d')
        # Create thumbnails directory inside the daily folder
        thumbs_dir = os.path.join(self.output_dir, date_str, "thumbnails")
        os.makedirs(thumbs_dir, exist_ok=True)
        
        # Determine extension? Usually webp or jpg from Douyin. 
        # But simpler to save as .jpg or just use video id + original ext if possible?
        # Let's save as .jpg for consistency in markdown, or just use ID.jpg if source is image.
        # Douyin URLs often have no extension or .webp parameters. 
        # I'll just save as .jpg.
        filename = f"{video.id}.jpg"
        file_path = os.path.join(thumbs_dir, filename)
        
        if os.path.exists(file_path):
            return True
            
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            response = requests.get(video.cover_url, headers=headers, stream=True, timeout=15)
            response.raise_for_status()
            
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            return True
        except Exception:
            return False

    def generate_report(self, videos: List[Video]):
        if not videos:
            return
            
        date_str = self.today.strftime('%Y-%m-%d')
        report_path = os.path.join(self.output_dir, date_str, "report.md")
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# 🎬 QuickTok Download Report - {date_str}\n\n")
            f.write(f"---\n")
            f.write(f"**Total Videos Processed:** {len(videos)}\n\n")
            f.write("| Preview | Video Information | Engagement & Stats |\n")
            f.write("| :--- | :--- | :--- |\n")
            
            for v in videos:
                # Format duration MM:SS
                seconds = v.duration // 1000
                minutes = seconds // 60
                rem_seconds = seconds % 60
                duration_str = f"{minutes:02}:{rem_seconds:02}"
                
                # Age calculation
                created_dt = datetime.fromtimestamp(v.create_time, tz=timezone.utc)
                age = (self.today - created_dt).days
                
                # Thumbnail path (relative for MD viewer)
                thumb_rel = f"thumbnails/{v.id}.jpg"
                
                # Metadata Column (ID + Description)
                # Cleaning description for MD table
                clean_desc = v.description.replace('\n', ' ').strip()
                if len(clean_desc) > 100:
                    clean_desc = clean_desc[:97] + "..."
                
                meta = f"**ID:** `{v.id}`<br><br>{clean_desc}"
                
                # Engagement Column
                # Highlight if it's a "Rocket" (Age 2-3 and likes > 3000)
                rocket_tag = "🚀 **ROCKET**" if (2 <= age <= 3 and v.digg_count > 3000) else "✅ GOOD"
                
                stats = (
                    f"{rocket_tag}<br>"
                    f"**Likes:** `{v.digg_count:,}`<br>"
                    f"**Age:** {age} days<br>"
                    f"**Res:** {v.width}x{v.height}<br>"
                    f"**Dur:** {duration_str}"
                )
                
                # Using HTML <img> to control width in preview
                img_html = f'<img src="{thumb_rel}" width="200" vspace="10">'
                
                f.write(f"| {img_html} | {meta} | {stats} |\n")
                
        logger.info(f"Generated improved report at {report_path}")

    def find_latest_json(self, search_path: Optional[str] = None) -> Optional[str]:
        json_files = []
        base_path = search_path or self.output_dir
        if not os.path.exists(base_path):
            return None
            
        for root, dirs, files in os.walk(base_path):
            for file in files:
                if file.endswith('.json'):
                    full_path = os.path.join(root, file)
                    json_files.append(full_path)
        
        if not json_files:
            return None
            
        # Sort by modification time (mtime) first, then by filename/path as a fallback.
        # mtime is generally more reliable for "freshly downloaded/updated" files.
        # Since the filenames are timestamped, the alphabetical sort also helps.
        json_files.sort(key=lambda x: (os.path.getmtime(x), x), reverse=True)
        return json_files[0]

def main():
    parser = argparse.ArgumentParser(description='Download Douyin videos from Apify JSON export.')
    parser.add_argument('json_path', nargs='?', help='Path to the Apify JSON export file. If not provided, finds the newest JSON in output dir.')
    parser.add_argument('--output', default='data', help='Root output directory for downloads')
    
    args = parser.parse_args()
    
    downloader = VideoDownloader(args.output)
    
    json_path = args.json_path
    if not json_path:
        search_dir = os.path.join(args.output, 'doyin.in')
        logger.info(f"No JSON path provided. Searching for newest JSON in '{search_dir}'...")
        json_path = downloader.find_latest_json(search_dir)
        if not json_path:
            logger.error(f"No JSON files found in {search_dir}")
            return
        logger.info(f"Found latest JSON file: {json_path}")
    
    videos = downloader.parse_json(json_path)
    
    if not videos:
        logger.info("No videos found to process.")
        return

    selected = downloader.filter_videos(videos)
    logger.info(f"Filtering complete. {len(selected)} out of {len(videos)} videos matched criteria.")
    
    if not selected:
        return
        
    success_count = 0
    downloaded_videos = []
    
    for vid in selected:
        # Download video
        if downloader.download_video(vid):
            success_count += 1
            downloaded_videos.append(vid)
            
        # Download thumbnail (silent fail ok)
        downloader.download_thumbnail(vid)
            
    # Generate report for successfully downloaded videos
    if downloaded_videos:
        downloader.generate_report(downloaded_videos)
            
    logger.info(f"Download complete. {success_count}/{len(selected)} videos downloaded.")

if __name__ == "__main__":
    main()
