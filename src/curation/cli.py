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

app = typer.Typer(help="LLM-based Image Curation CLI")
console = Console()

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
        batch_size=batch_size
    )
    
    # Initialize pipeline
    try:
        from src.curation.scorer import ImageScorer
        from src.telegram.database import TelegramImportDB
        
        scorer = ImageScorer(api_key=api_key)
        
        # Initialize DB
        db_path = Path("data/telegram_imports.db")
        db = TelegramImportDB(db_path) if db_path.exists() else None
        
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
    # Find all leaf directories that contain images?
    # Or just iterate over channel folders.
    # Structure: data/incoming/Channel/Timestamp/
    # We should iterate over Timestamp folders.
    
    # Simplification: walk and find dirs with images?
    # Or just iterate incoming/*/*
    
    # For MVP, let's assume standard structure: incoming/Channel/Timestamp
    if not incoming_dir.exists():
        console.print(f"[red]Directory not found: {incoming_dir}[/red]")
        raise typer.Exit(1)

    channels = [d for d in incoming_dir.iterdir() if d.is_dir()]
    total_processed = 0
    
    for channel in channels:
        timestamps = [d for d in channel.iterdir() if d.is_dir()]
        for ts_folder in timestamps:
            console.print(f"\n[bold]Processing:[/bold] {ts_folder}")
            # Call curate logic (reuse or subprocess?)
            # Reuse logic
            config = CurationConfig(threshold=threshold, dry_run=dry_run, batch_size=batch_size)
            try:
                from src.curation.scorer import ImageScorer
                from src.telegram.database import TelegramImportDB

                scorer = ImageScorer() # Env var expected
                
                db_path = Path("data/telegram_imports.db")
                db = TelegramImportDB(db_path) if db_path.exists() else None
                
                pipeline = CurationPipeline(config=config, scorer=scorer, db=db)
                
                report = asyncio.run(pipeline.curate_folder(ts_folder))
                _print_report(report)
                total_processed += report.total_images
            except Exception as e:
                console.print(f"[red]Failed to process {ts_folder}: {e}[/red]")

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
