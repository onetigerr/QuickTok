#!/usr/bin/env python3
"""
Monitor open file descriptors during curation process.
Run this script to test if file descriptors are being properly released.
"""
import os
import psutil
import time
import subprocess
import sys

def get_open_files_count():
    """Get current process's open file descriptors count."""
    try:
        process = psutil.Process()
        return process.num_fds()
    except:
        # Fallback for macOS
        pid = os.getpid()
        result = subprocess.run(['lsof', '-p', str(pid)], capture_output=True, text=True)
        return len(result.stdout.strip().split('\n')) - 1  # -1 for header

def monitor_curate_all():
    """Run curate-all and monitor file descriptors."""
    print("Starting file descriptor monitoring...")
    print(f"Initial FD count: {get_open_files_count()}")
    
    # Import and run the curation pipeline
    from src.curation.cli import app
    import asyncio
    from pathlib import Path
    from src.curation.pipeline import CurationPipeline, CurationConfig
    from src.curation.scorer import ImageScorer
    from src.telegram.database import TelegramImportDB
    
    async def test_run():
        config = CurationConfig(threshold=7.0, dry_run=False, batch_size=5)
        scorer = ImageScorer()
        
        db_path = Path("data/telegram_imports.db")
        db = TelegramImportDB(db_path) if db_path.exists() else None
        
        incoming_dir = Path("data/incoming")
        channels = [d for d in incoming_dir.iterdir() if d.is_dir()]
        
        processed_folders = 0
        for channel in channels:
            timestamps = [d for d in channel.iterdir() if d.is_dir()]
            for ts_folder in timestamps[:5]:  # Limit to first 5 folders for testing
                print(f"\nProcessing: {ts_folder}")
                print(f"FD count before: {get_open_files_count()}")
                
                pipeline = CurationPipeline(config=config, scorer=scorer, db=db)
                
                try:
                    report = await pipeline.curate_folder(ts_folder)
                    print(f"Total images: {report.total_images}")
                    print(f"FD count after: {get_open_files_count()}")
                    processed_folders += 1
                except Exception as e:
                    print(f"Error: {e}")
                
                # Check if we're leaking FDs
                if processed_folders > 0 and processed_folders % 2 == 0:
                    current_fds = get_open_files_count()
                    print(f"\n=== After {processed_folders} folders: {current_fds} FDs ===\n")
    
    asyncio.run(test_run())
    
    print(f"\nFinal FD count: {get_open_files_count()}")

if __name__ == "__main__":
    monitor_curate_all()
