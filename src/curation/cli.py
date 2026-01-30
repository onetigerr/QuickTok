import warnings
import typer

import asyncio
from pathlib import Path
from rich import print
from rich.table import Table
from rich.console import Console
from typing import Optional

from src.curation.pipeline import CurationPipeline, CurationConfig
from src.curation.models import CurationReport
from dotenv import load_dotenv

# Load env variables including GROQ_API_KEY
load_dotenv()

# Allow flags to be specified anywhere (before or after arguments)
CONTEXT_SETTINGS = {"allow_interspersed_args": True}
app = typer.Typer(help="LLM-based Image Curation CLI", context_settings=CONTEXT_SETTINGS)
console = Console()

# Global state for force flag
class GlobalState:
    force: bool = False

global_state = GlobalState()

@app.callback()
def main_callback(
    force: bool = typer.Option(False, "--force", "-f", help="Force re-curation even if already processed")
):
    """Global options for all commands."""
    global_state.force = force

@app.command()
def curate(
    folder: Path = typer.Argument(..., help="Path to folder containing images", exists=True, file_okay=False, dir_okay=True),
    threshold: float = typer.Option(7.0, "--threshold", "-t", help="Minimum combined score to select"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n", help="Simulate without moving files"),
    batch_size: int = typer.Option(5, "--batch-size", "-b", help="Number of images per API call"),
    api_key: Optional[str] = typer.Option(None, envvar="GROQ_API_KEY", help="Groq API Key (or set GROQ_API_KEY env var)"),
):
    """
    Curate images in a specific folder.
    Images with score >= threshold are moved to data/curated.
    """
    config = CurationConfig(
        threshold=threshold,
        dry_run=dry_run,
        batch_size=batch_size,
        force=global_state.force
    )
    
    # Initialize pipeline
    try:
        from src.curation.scorer import ImageScorer
        from src.telegram.database import TelegramImportDB
        
        scorer = ImageScorer(api_key=api_key)
        
        # Initialize DB (will auto-create if doesn't exist)
        db_path = Path("data/telegram_imports.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db = TelegramImportDB(db_path)
        
        pipeline = CurationPipeline(config=config, scorer=scorer, db=db)
    except Exception as e:
        console.print(f"[bold red]Error initializing pipeline:[/bold red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[bold blue]Starting curation for:[/bold blue] {folder}")
    if dry_run:
        console.print("[yellow]DRY RUN MODE: No files will be moved[/yellow]")

    # Run async pipeline
    report = asyncio.run(pipeline.curate_folder(folder))
    
    _print_report(report)

@app.command()
def curate_all(
    incoming_dir: Path = typer.Argument(Path("data/incoming"), help="Root incoming directory"),
    threshold: float = typer.Option(7.0, "--threshold", "-t"),
    dry_run: bool = typer.Option(False, "--dry-run", "-n"),
    batch_size: int = typer.Option(5, "--batch-size", "-b"),
):
    """
    Process all subfolders in data/incoming recursively.
    """
    if not incoming_dir.exists():
        console.print(f"[red]Directory not found: {incoming_dir}[/red]")
        raise typer.Exit(1)

    # Initialize shared resources once
    try:
        from src.curation.scorer import ImageScorer
        from src.telegram.database import TelegramImportDB
    except ImportError as e:
        console.print(f"[red]Failed to import dependencies: {e}[/red]")
        raise typer.Exit(1)

    async def _curate_all_async():
        # Initialize dependencies inside the loop to ensure clean async context
        # Although ImageScorer might be robust, it's safer to init here.
        config = CurationConfig(threshold=threshold, dry_run=dry_run, batch_size=batch_size, force=global_state.force)
        
        try:
            scorer = ImageScorer() # Env var expected
        except Exception as e:
            console.print(f"[red]Failed to initialize Scorer:[/red] {e}")
            return 0

        db_path = Path("data/telegram_imports.db")
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db = TelegramImportDB(db_path)
        
        # We can reuse the same pipeline instance as well, or create new ones.
        # Reusing is better if it doesn't hold state per folder. 
        # CurationPipeline seems stateless regarding folder (passed in method).
        # It holds 'consecutive_errors' state which is desirable to circuit-break globally?
        # Or per folder?
        # The user probably wants per-run circuit breaker, or at least per-folder reset?
        # The original code re-initialized pipeline per folder, so consecutive_errors reset per folder?
        # Let's check pipeline.py.
        # Pipeline.__init__: consecutive_errors = 0.
        # So it resets per folder in old code.
        # If we reuse pipeline, consecutive_errors accumulates.
        # If we want to mimic old behavior (reset error count per folder), we should manually reset or re-init.
        # Re-initializing Pipeline is cheap (just object creation).
        
        # Actually pipeline.curate_folder resets consecutive_errors on success.
        # But if a folder fails completely, we might want to continue to next?
        # If we share pipeline, and one folder triggers 3 errors, pipeline stops everything?
        # Pipeline.curate_folder loop breaks on consecutive_errors.
        # But afterwards, consecutive_errors is still high.
        # So we should probably re-create pipeline or reset it.
        # Let's re-create pipeline per folder to be safe and isolated, 
        # BUT REUSE SCORER. The Scorer is the heavy resource.
        
        channels = [d for d in incoming_dir.iterdir() if d.is_dir()]
        total_processed_count = 0
        
        for channel in channels:
            timestamps = [d for d in channel.iterdir() if d.is_dir()]
            for ts_folder in timestamps:
                console.print(f"\n[bold]Processing:[/bold] {ts_folder}")
                
                pipeline = CurationPipeline(config=config, scorer=scorer, db=db)
                
                try:
                    report = await pipeline.curate_folder(ts_folder)
                    _print_report(report)
                    total_processed_count += report.total_images
                except Exception as e:
                    console.print(f"[red]Failed to process {ts_folder}: {e}[/red]")
                    # Continue to next folder
        
        return total_processed_count

    # Run the single async entry point
    total_processed = asyncio.run(_curate_all_async())
    
    console.print(f"\n[bold green]Finished processing all folders. Total images: {total_processed}[/bold green]")

def _print_report(report: CurationReport):
    table = Table(title="Curation Report")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Total Images", str(report.total_images))
    table.add_row("Curated (Selected)", str(report.curated_count))
    table.add_row("Rejected (Explicit)", str(report.rejected_explicit))
    table.add_row("Rejected (Low Score)", str(report.rejected_low_score))
    table.add_row("Errors", str(report.errors))
    table.add_row("Avg Score", str(report.avg_score))
    
    console.print(table)
    
    if report.results:
        # Show breakdown of scores
        results_table = Table(title="Detailed Results", show_header=True)
        results_table.add_column("File")
        results_table.add_column("Score")
        results_table.add_column("Result")
        results_table.add_column("Destination")
        
        for r in report.results:
            score_str = f"{r.score.combined_score:.1f}" if r.score else "N/A"
            if r.score and r.score.is_explicit:
                score_str = "[red]EXPLICIT[/red]"
            
            status = "[green]SELECTED[/green]" if r.curated else "[dim]REJECTED[/dim]"
            if r.error:
                status = f"[red]ERROR: {r.error}[/red]"
            
            dest_str = str(r.destination) if r.destination else "-"
            
            # Highlight if destination has Model name (simple check)
            if "/" in dest_str and "Yuiwoo" in dest_str: # Just an example check not needed in code
                pass

            results_table.add_row(r.source_path.name, score_str, status, dest_str)
            
        console.print(results_table)

if __name__ == "__main__":
    app()
