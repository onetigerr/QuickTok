from pathlib import Path
from typing import List, Optional
import shutil
import asyncio
from datetime import datetime

from src.curation.models import ImageScore, CurationConfig, CurationReport, CurationResult
from src.curation.scorer import ImageScorer
# We utilize loose coupling or type hint as "Any" to avoid circular verification issues if module not ready, 
# but preferably we import the type.
from typing import Any

class CurationPipeline:
    def __init__(
        self,
        config: CurationConfig = CurationConfig(),
        scorer: Optional[ImageScorer] = None,
        db: Any = None  # TelegramImportDB
    ):
        self.config = config
        self.scorer = scorer or ImageScorer()
        self.db = db
        self.curated_base_dir = Path("data/curated")
        self.consecutive_errors = 0
        self.max_consecutive_errors = 3
    
    # ... (curate_folder and _process_batch remain unchanged)

    async def curate_folder(self, folder: Path) -> CurationReport:
        """Process all images in a folder."""
        start_time = datetime.now()
        image_files = self._find_images(folder)
        
        results: List[CurationResult] = []
        
        # Process in batches
        for i in range(0, len(image_files), self.config.batch_size):
            if self.consecutive_errors >= self.max_consecutive_errors:
                print("Circuit breaker triggered. Stopping curation.")
                break
                
            batch_paths = image_files[i : i + self.config.batch_size]
            batch_results = await self._process_batch(batch_paths)
            results.extend(batch_results)
            
        # Aggregate report
        return self._create_report(folder, results, start_time)

    async def _process_batch(self, paths: List[Path]) -> List[CurationResult]:
        """Process a batch of images."""
        batch_results = []
        try:
            scores = await self.scorer.score_batch(paths)
            self.consecutive_errors = 0  # Reset on success
            
            for path, score in zip(paths, scores):
                curated = self._should_curate(score)
                dest = None
                
                if curated:
                    if not self.config.dry_run:
                        dest = self._move_to_curated(path)
                    else:
                        # Calculate dest for reporting only
                        dest = self._move_to_curated(path, dry_run=True)
                
                batch_results.append(CurationResult(
                    source_path=path,
                    score=score,
                    curated=curated,
                    destination=dest
                ))
                
        except Exception as e:
            # Entire batch failed
            self.consecutive_errors += 1
            error_msg = str(e)
            for path in paths:
                batch_results.append(CurationResult(
                    source_path=path,
                    error=error_msg,
                    curated=False
                ))
        
        return batch_results

    def _should_curate(self, score: ImageScore) -> bool:
        """Check if image meets criteria."""
        if score.is_explicit:
            return False
        return score.combined_score >= self.config.threshold

    def _move_to_curated(self, src: Path, dry_run: bool = False) -> Path:
        """Move file to curated directory using Model/Date structure if available."""
        destination_subdir = None
        
        try:
            # relative_to data/incoming
            base_incoming = Path("data/incoming").resolve()
            src_abs = src.resolve()
            
            # Try both absolute and direct
            try:
                relative_full = src_abs.relative_to(base_incoming)
            except ValueError:
                # If src was passed as absolute but different mounting?
                # Try blindly string matching if safe, or ensure we find the "incoming" segment
                parts = src.parts
                if "incoming" in parts:
                    idx = parts.index("incoming")
                    relative_full = Path(*parts[idx+1:])
                else:
                    raise ValueError("Not in incoming")

            # The folder containing the image corresponds to the DB entry
            # i.e. CCumpot/2026-01-22_07-01-58
            db_lookup_path = str(relative_full.parent)
            
            if self.db:
                model_name = self.db.get_model_by_path(db_lookup_path)
                if model_name and model_name != "Unknown":
                    # Structure: Model_Name/Timestamp/Image.jpg
                    timestamp_folder = relative_full.parent.name
                    destination_subdir = Path(model_name) / timestamp_folder / relative_full.name
        except Exception as e:
            # print(f"DEBUG: Path resolution failed: {e}") 
            pass
            
        if not destination_subdir:
            # Fallback: maintain original structure
            try:
                destination_subdir = src.relative_to(Path("data/incoming"))
            except ValueError:
                destination_subdir = src.name

        dest = self.curated_base_dir / destination_subdir
        
        if not dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(str(src), str(dest))
            
        return dest

    def _find_images(self, folder: Path) -> List[Path]:
        """Recursively find image files."""
        extensions = {".jpg", ".jpeg", ".png", ".webp"}
        files = [
            f for f in folder.rglob("*") 
            if f.suffix.lower() in extensions and f.is_file()
        ]
        return sorted(files)

    def _create_report(
        self, 
        source: Path, 
        results: List[CurationResult], 
        start: datetime
    ) -> CurationReport:
        """Generate summary report."""
        total = len(results)
        curated = sum(1 for r in results if r.curated)
        errors = sum(1 for r in results if r.error)
        
        explicit = 0
        low_score = 0
        total_score = 0.0
        scored_count = 0
        
        for r in results:
            if r.score:
                scored_count += 1
                total_score += r.score.combined_score
                if r.score.is_explicit:
                    explicit += 1
                elif r.score.combined_score < self.config.threshold:
                    low_score += 1
                    
        avg_score = total_score / scored_count if scored_count > 0 else 0.0
        
        return CurationReport(
            timestamp=start,
            source_folder=str(source),
            total_images=total,
            curated_count=curated,
            rejected_explicit=explicit,
            rejected_low_score=low_score,
            errors=errors,
            avg_score=round(avg_score, 2),
            results=results
        )
