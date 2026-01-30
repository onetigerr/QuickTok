import asyncio
import logging
from pathlib import Path
from datetime import datetime
from telethon import TelegramClient
from telethon.tl.types import Message, MessageMediaPhoto
from telethon.errors import ChannelPrivateError

from .models import ImportResult, ImportedPost, ContentFormat
from .database import TelegramImportDB
from .adapters.base import BaseAdapter

logger = logging.getLogger(__name__)

class TelegramClientWrapper:
    def __init__(self, session_path: Path, db: TelegramImportDB):
        self.session_path = session_path
        self.db = db
        # We assume api_id/hash are embedded in the session or not needed if we are just using the session file
        # But Telethon usually requires them. 
        # For this design, we'll assume they are loaded from env vars by the caller or passed in.
        # The design specifies using a session file.
        # Telethon still needs api_id/hash even with session file usually, unless it's a string session?
        # The design shows `__init__(self, session_path: Path, api_id: int, api_hash: str)`
        # I will update the init to match the design.
        self.client = None

    async def connect(self, api_id: int, api_hash: str):
        """Connect to Telegram."""
        self.client = TelegramClient(str(self.session_path), api_id, api_hash)
        await self.client.connect()
        if not await self.client.is_user_authorized():
            raise RuntimeError("Session is not authorized. Please log in manually first.")

    async def import_channel(
        self, 
        channel_name: str, 
        adapter: BaseAdapter,
        limit: int | None = None,
        incoming_dir: Path = Path("data/incoming")
    ) -> ImportResult:
        """Main import method."""
        if not self.client:
            raise RuntimeError("Client not connected")

        result = ImportResult(
            total_processed=0,
            downloaded=0,
            skipped_duplicates=0,
            errors=0
        )
        
        consecutive_errors = 0
        MAX_CONSECUTIVE_ERRORS = 3
        
        try:
            entity = await self.client.get_entity(channel_name)
        except ValueError:
            logger.error(f"Channel {channel_name} not found")
            result.errors += 1
            return result
        except Exception as e:
            logger.error(f"Error getting entity {channel_name}: {e}")
            result.errors += 1
            return result

        # Iterate posts from newest to oldest
        # We iterate without a limit, but stop when we've downloaded enough new posts
        async for message in self.client.iter_messages(entity):
            result.total_processed += 1
            
            # 1. Filter
            if not adapter.filter(message):
                continue
                
            # 2. Check duplicates - but don't stop, just skip and continue
            is_duplicate = self.db.post_exists(channel_name, message.id)
            if is_duplicate:
                result.skipped_duplicates += 1
                logger.info(f"Skipping duplicate post {message.id}")
                # Continue to next post instead of counting towards limit
                continue
            else:
                logger.info(f"Processing new post {message.id}")
            
            # 3. Process & Download
            try:
                metadata = adapter.extract_metadata(message)
                
                # Format timestamp folder name
                timestamp_str = message.date.strftime("%Y-%m-%d_%H-%M-%S")
                save_dir = incoming_dir / channel_name / timestamp_str
                save_dir.mkdir(parents=True, exist_ok=True)
                
                # Download media from post and comments
                downloaded_paths = await self.download_media_with_comments(message, save_dir, entity)
                
                if not downloaded_paths:
                    logger.warning(f"No media downloaded for post {message.id}")
                    # Treat as non-fatal, maybe just filter said so?
                
                # We save relative path to the folder, as there might be multiple files
                relative_path = f"{channel_name}/{timestamp_str}"
                
                post_record = ImportedPost(
                    channel_name=channel_name,
                    post_id=message.id,
                    date=message.date,
                    model_name=metadata.model_name,
                    set_name=metadata.set_name,
                    content_format=metadata.content_format,
                    file_path=relative_path
                )
                
                self.db.save_post(post_record)
                result.downloaded += 1
                consecutive_errors = 0 # Reset on success
                
                # Check if we've reached the limit of NEW posts downloaded
                if limit is not None and result.downloaded >= limit:
                    logger.info(f"Reached limit of {limit} downloaded posts")
                    break
                
            except Exception as e:
                logger.error(f"Error processing post {message.id}: {e}")
                result.errors += 1
                consecutive_errors += 1
                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    logger.error("Too many consecutive errors. Stopping import.")
                    result.stopped_early = True
                    break
        
        return result

    async def download_media_with_comments(self, message: Message, dest_folder: Path, channel_entity) -> list[Path]:
        """Downloads all media from the message and its comments into the specified folder."""
        from .settings import MAX_FILE_SIZE_BYTES
        
        paths = []
        
        # Download main post media
        try:
            # Check file size before downloading
            if message.media and hasattr(message.media, 'document'):
                file_size = getattr(message.media.document, 'size', 0)
                if file_size > MAX_FILE_SIZE_BYTES:
                    logger.warning(f"Skipping main post media: file size {file_size / 1024 / 1024:.2f}MB exceeds limit")
                else:
                    path = await self.client.download_media(message, file=dest_folder)
                    if path:
                        paths.append(Path(path))
                        logger.info(f"Downloaded main post media: {path}")
            elif message.media:
                # Photo doesn't have size attribute, download directly
                path = await self.client.download_media(message, file=dest_folder)
                if path:
                    paths.append(Path(path))
                    logger.info(f"Downloaded main post media: {path}")
        except Exception as e:
            logger.error(f"Download failed for main post: {e}")
            raise e
        
        # Download media from comments
        try:
            comment_count = 0
            comments_checked = 0
            logger.info(f"Checking comments for post {message.id}...")
            
            async for comment in self.client.iter_messages(channel_entity, reply_to=message.id):
                comments_checked += 1
                if comment.media:
                    try:
                        # Check file size for comments too
                        should_download = True
                        if hasattr(comment.media, 'document'):
                            file_size = getattr(comment.media.document, 'size', 0)
                            if file_size > MAX_FILE_SIZE_BYTES:
                                logger.warning(f"Skipping comment media: file size {file_size / 1024 / 1024:.2f}MB exceeds limit")
                                should_download = False
                        
                        if should_download:
                            path = await self.client.download_media(comment, file=dest_folder)
                            if path:
                                paths.append(Path(path))
                                comment_count += 1
                                logger.info(f"Downloaded comment media: {path}")
                    except Exception as e:
                        logger.warning(f"Failed to download media from comment {comment.id}: {e}")
                        # Continue with other comments even if one fails
                        continue
            
            logger.info(f"Checked {comments_checked} comments, downloaded {comment_count} images from comments")
        except Exception as e:
            logger.warning(f"Error iterating comments: {e}")
            # Don't fail the entire post if comment iteration fails
            
        return paths
