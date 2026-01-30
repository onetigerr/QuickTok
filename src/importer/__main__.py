import asyncio
import argparse
import logging
from pathlib import Path
from src.telegram.client import TelegramClientWrapper
from src.telegram.database import TelegramImportDB
from src.telegram.adapters.ccumpot import CCumpotAdapter
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def run_import(channel_name: str, limit: int | None):
    # Constants
    SESSIONS_DIR = Path("data/sessions")
    DATABASE_PATH = Path("data/telegram_imports.db")
    
    # 1. Setup Session
    # We look for any .session file in the directory or a specific one if we knew the phone number.
    # The design specifies using existing .session files.
    # Let's try to find '*_session.session' as seen in list_dir.
    session_files = list(SESSIONS_DIR.glob("*.session"))
    if not session_files:
        logger.error("No session files found in data/sessions/")
        return
    
    session_path = session_files[0]
    logger.info(f"Using session: {session_path}")
    
    # 2. Setup DB
    db = TelegramImportDB(DATABASE_PATH)
    
    # 3. Setup Adapter
    adapters = {
        "ccumpot": CCumpotAdapter(),
    }
    
    adapter = adapters.get(channel_name.lower())
    if not adapter:
        logger.error(f"Unknown channel: {channel_name}. Available: {list(adapters.keys())}")
        return

    # 4. Init Client
    load_dotenv()
    
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")
    
    if not api_id or not api_hash:
        logger.error("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env")
        return

    client_wrapper = TelegramClientWrapper(session_path, db)
    
    try:
        await client_wrapper.connect(int(api_id), api_hash)
        logger.info("Connected to Telegram")
        
        logger.info(f"Starting import for channel {channel_name} with limit {limit}")
        result = await client_wrapper.import_channel(adapter.channel_name, adapter, limit)
        
        logger.info(f"Import finished: {result}")
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        if client_wrapper.client:
            await client_wrapper.client.disconnect()

def main():
    parser = argparse.ArgumentParser(description="Import content from Telegram channels")
    parser.add_argument("--channel", required=True, help="Channel name (e.g., CCumpot)")
    parser.add_argument("--limit", type=int, default=None, help="Max posts to process")
    args = parser.parse_args()
    
    asyncio.run(run_import(args.channel, args.limit))

if __name__ == "__main__":
    main()
