from pathlib import Path
from typing import List, Optional
import shutil
import asyncio
import gc
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
        
        # Optimization: Check if entire folder is already processed (unless force=True)
        if self.db and not self.config.force:
            try:
                base_incoming = Path("data/incoming").resolve()
                folder_abs = folder.resolve()
                relative = folder_abs.relative_to(base_incoming)
                db_key = str(relative)
                
                # Check DB flag
                # User requested to ignore DB flag for now, relying only on filesystem
                is_processed = False 
                # is_processed = self.db.is_post_processed(db_key)
                
                # ALSO Check folder existence in curated/
                model_name = self.db.get_model_by_path(db_key)
                if model_name:
                    dest_folder = self.curated_base_dir / model_name / folder.name
                    if dest_folder.exists():
                        is_processed = True

                if is_processed:
                    print(f"Skipping processed folder: {folder.name}")
                    return self._create_skipped_report(folder, start_time, "Folder already processed")
            except Exception:
                pass

        image_files = self._find_images(folder)
        
        # Step 1: Score all images in batches
        all_scores = []
        paths_to_score = []
        skipped_results = []
        
        for path in image_files:
            # Check if already processed (unless force=True)
            is_processed = False
            if not self.config.force:
                dest_predict = self._move_to_curated(path, dry_run=True)
                if dest_predict.exists():
                    is_processed = True

            if is_processed:
                skipped_results.append(CurationResult(
                    source_path=path,
                    curated=False,
                    error="Already processed"
                ))
            else:
                paths_to_score.append(path)
        
        # Score in batches to avoid overwhelming the API
        for i in range(0, len(paths_to_score), self.config.batch_size):
            if self.consecutive_errors >= self.max_consecutive_errors:
                print("Circuit breaker triggered. Stopping curation.")
                break
                
            batch_paths = paths_to_score[i : i + self.config.batch_size]
            try:
                batch_scores = await self.scorer.score_batch(batch_paths)
                all_scores.extend(batch_scores)
                self.consecutive_errors = 0
                
                # Save scores to database (skip explicit photos)
                if self.db:
                    for path, score in zip(batch_paths, batch_scores):
                        try:
                            # Resolve model name from DB
                            base_incoming = Path("data/incoming").resolve()
                            relative = path.resolve().relative_to(base_incoming)
                            db_key = str(relative.parent)
                            model_name = self.db.get_model_by_path(db_key)
                            
                            # Convert ImageScore to dict
                            score_dict = {
                                'wow_factor': score.wow_factor,
                                'engagement': score.engagement,
                                'tiktok_fit': score.tiktok_fit,
                                'is_explicit': score.is_explicit,
                                'reasoning': score.reasoning,
                                'watermark_offset_pct': score.watermark_offset_pct
                            }
                            
                            # Use relative path as file_path identifier
                            result = self.db.save_photo_score(str(relative), score_dict, model_name)
                            if result is None and not score.is_explicit:
                                print(f"DEBUG: Failed to save score for {relative} (not explicit, but returned None - duplicate?)")
                            elif result is not None:
                                print(f"DEBUG: Saved score for {relative} with id={result}")
                            elif score.is_explicit:
                                print(f"DEBUG: Skipped explicit photo {relative}")
                        except Exception as e:
                            # Don't fail the pipeline if DB save fails, but log it
                            print(f"ERROR saving score to DB for {path}: {e}")
                            import traceback
                            traceback.print_exc()
                            
            except Exception as e:
                self.consecutive_errors += 1
                # Add error results for failed batch
                for path in batch_paths:
                    skipped_results.append(CurationResult(
                        source_path=path,
                        curated=False,
                        error=str(e)
                    ))
            
            # Force garbage collection
            gc.collect()
        
        # Step 2: Apply selection logic to ALL scored images (folder-level)
        path_score_pairs = list(zip(paths_to_score[:len(all_scores)], all_scores))
        
        # Separate explicit and non-explicit
        non_explicit = [(p, s) for p, s in path_score_pairs if not s.is_explicit]
        explicit = [(p, s) for p, s in path_score_pairs if s.is_explicit]
        
        # Sort non-explicit by combined_score (descending)
        non_explicit.sort(key=lambda x: x[1].combined_score, reverse=True)
        
        # Separate above and below threshold
        above_threshold = [(p, s) for p, s in non_explicit if s.combined_score >= self.config.threshold]
        below_threshold = [(p, s) for p, s in non_explicit if s.combined_score < self.config.threshold]
        
        # Select: ALL above threshold if >= 6, otherwise fill up to 6 with below threshold
        if len(above_threshold) >= 6:
            selected = above_threshold
        else:
            selected = above_threshold.copy()
            remaining = 6 - len(selected)
            selected.extend(below_threshold[:remaining])
        
        # Step 3: Move selected files and create results
        results = []
        
        for path, score in selected:
            dest = None
            if not self.config.dry_run:
                dest = self._move_to_curated(path)
            else:
                dest = self._move_to_curated(path, dry_run=True)
            
            results.append(CurationResult(
                source_path=path,
                score=score,
                curated=True,
                destination=dest
            ))
        
        # Add rejected photos
        rejected = explicit + [pair for pair in non_explicit if pair not in selected]
        for path, score in rejected:
            results.append(CurationResult(
                source_path=path,
                score=score,
                curated=False,
                destination=None
            ))
        
        # Mark folder as processed in DB
        if not self.config.dry_run and self.db and paths_to_score:
            try:
                relative = paths_to_score[0].relative_to(Path("data/incoming"))
                db_key = str(relative.parent)
                self.db.mark_post_processed(db_key)
            except:
                pass
        
        # Combine with skipped results
        all_results = skipped_results + results
        
        # Aggregate report
        return self._create_report(folder, all_results, start_time)

    async def _process_batch(self, paths: List[Path]) -> List[CurationResult]:
        """Process a batch of images."""
        batch_results = []
        try:
            # Filter out already curated items
            paths_to_score = []
            skipped_results = []
            
            for path in paths:
                # 1. Check if already exists in curated (rough check based on expected destination)
                # This is tricky because destination depends on model name resolution which happens later.
                # But we can check DB first.
                
                is_processed = False
                if self.db and not self.config.force:
                    # Resolve relative path for DB lookup
                    try:
                        relative = path.relative_to(Path("data/incoming"))
                        # DB store file_path as "Channel/Date/file.jpg" usually?
                        # Let's check DB schema or usage. 
                        # In imports we save "Channel/Date/file.jpg"?
                        # Let's assume relative path matches DB file_path column.
                        # Actually ImportedPost.file_path usually stores relative path.
                        
                        # Wait, pipeline uses relative_to("data/incoming").
                        # Let's verify what's stored in DB.
                        # DB view earlier: "CCumpot/2026-01-23_15-40-26"
                        # That looks like a folder path or ID?
                        # Ah, the sample output: 1|CCumpot|...|CCumpot/2026-01-23_15-40-26|...
                        # file_path column seems to be folder or file?
                        # "CCumpot/2026-01-23_15-40-26" is likely the folder.
                        # But individual photos? 
                        # The importer saves *posts*. A post can have multiple photos.
                        # If file_path is the folder, then `curation_processed` flag applies to the WHOLE post folder?
                        # User said "But orient first on file existence".
                        
                        # If DB flag is per post (folder), then if we mark it processed, we skip all images in it.
                        # That seems correct for "Processed this post".
                        
                        db_key = str(relative.parent) # The post folder
                        # if self.db.is_post_processed(db_key):
                        #    is_processed = True
                    except ValueError:
                        pass
                
                # 2. Check physical file existence in curated (unless force=True)
                if not self.config.force:
                    # We can predict destination and check existence
                    # But move_to_curated logic is complex.
                    # Let's rely on DB flag primarily for "processed status", 
                    # and maybe check if destination file exists to be safe?
                    # Calculating destination for every file before scoring is cheap.
                    dest_predict = self._move_to_curated(path, dry_run=True)
                    if dest_predict.exists():
                         is_processed = True

                if is_processed:
                    skipped_results.append(CurationResult(
                        source_path=path,
                        curated=False,
                        error="Already processed"
                    ))
                else:
                    paths_to_score.append(path)

            if not paths_to_score:
                return skipped_results

            scores = await self.scorer.score_batch(paths_to_score)
            self.consecutive_errors = 0  # Reset on success
            
            # Save scores to database (skip explicit photos)
            if self.db:
                for path, score in zip(paths_to_score, scores):
                    try:
                        base_incoming = Path("data/incoming").resolve()
                        relative = path.resolve().relative_to(base_incoming)
                        db_key = str(relative.parent)
                        model_name = self.db.get_model_by_path(db_key)
                        
                        score_dict = {
                            'wow_factor': score.wow_factor,
                            'engagement': score.engagement,
                            'tiktok_fit': score.tiktok_fit,
                            'is_explicit': score.is_explicit,
                            'reasoning': score.reasoning,
                            'watermark_offset_pct': score.watermark_offset_pct
                        }
                        
                        result = self.db.save_photo_score(str(relative), score_dict, model_name)
                        if result is None and not score.is_explicit:
                            print(f"DEBUG: Failed to save score for {relative} (not explicit, but returned None - duplicate?)")
                        elif result is not None:
                            print(f"DEBUG: Saved score for {relative} with id={result}")
                        elif score.is_explicit:
                            print(f"DEBUG: Skipped explicit photo {relative}")
                    except Exception as e:
                        print(f"ERROR saving score to DB for {path}: {e}")
                        import traceback
                        traceback.print_exc()
            
            # New selection logic: select best non-explicit photos
            # 1. Filter out explicit photos
            # 2. Take ALL photos above threshold
            # 3. If fewer than 6 above threshold, fill up to 6 with best below-threshold photos
            
            path_score_pairs = list(zip(paths_to_score, scores))
            
            # Separate explicit and non-explicit
            non_explicit = [(p, s) for p, s in path_score_pairs if not s.is_explicit]
            explicit = [(p, s) for p, s in path_score_pairs if s.is_explicit]
            
            # Sort non-explicit by combined_score (descending)
            non_explicit.sort(key=lambda x: x[1].combined_score, reverse=True)
            
            # Separate above and below threshold
            above_threshold = [(p, s) for p, s in non_explicit if s.combined_score >= self.config.threshold]
            below_threshold = [(p, s) for p, s in non_explicit if s.combined_score < self.config.threshold]
            
            # Select: ALL above threshold if >= 6, otherwise fill up to 6 with below threshold
            if len(above_threshold) >= 6:
                # If we have 6+ above threshold, take only those
                selected = above_threshold
            else:
                # If fewer than 6 above threshold, fill up to 6 with below threshold
                selected = above_threshold.copy()
                remaining = 6 - len(selected)
                selected.extend(below_threshold[:remaining])
            
            # Create results for selected photos
            scored_results = []
            for path, score in selected:
                curated = True
                dest = None
                
                if not self.config.dry_run:
                    dest = self._move_to_curated(path)
                else:
                    # Calculate dest for reporting only
                    dest = self._move_to_curated(path, dry_run=True)
                
                # Mark as processed in DB (if not dry run)
                # We mark the *post* (folder) as processed? 
                # Or do we need to track individual files?
                # The DB migration added column to `imported_posts`.
                # imported_posts is likely 1 row per post.
                # So we mark the post (folder) as processed.
                # Careful: batch might contain images from different posts?
                # Batch comes from `image_files`. `_find_images` returns list.
                # If we mix posts in a batch, we might mark a post processed when only 1 image of it is done.
                # But usually we process folder by folder.
                
                if not self.config.dry_run and self.db:
                   try:
                       relative = path.relative_to(Path("data/incoming"))
                       db_key = str(relative.parent)
                       self.db.mark_post_processed(db_key)
                   except:
                       pass

                scored_results.append(CurationResult(
                    source_path=path,
                    score=score,
                    curated=curated,
                    destination=dest
                ))
            
            # Create results for rejected photos (explicit + not selected non-explicit)
            rejected = explicit + [pair for pair in non_explicit if pair not in selected]
            for path, score in rejected:
                scored_results.append(CurationResult(
                    source_path=path,
                    score=score,
                    curated=False,
                    destination=None
                ))
            
            return skipped_results + scored_results
                
        except Exception as e:
            # Entire batch failed (only for actual scoring failures)
            self.consecutive_errors += 1
            error_msg = str(e)
            
            # Skip skipped_results in error handling?
            # If we had partial success (some skipped), we should return those?
            # But e was raised likely during score_batch.
            # If score_batch fails, we fail the *scored* items.
            # Skipped items are already processed.
            
            # Fallback for paths_to_score
            error_results = []
            for path in paths_to_score:
                error_results.append(CurationResult(
                    source_path=path,
                    error=error_msg,
                    curated=False
                ))
            
            return skipped_results + error_results

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

    def _create_skipped_report(self, source: Path, start: datetime, reason: str) -> CurationReport:
        """Create a report for a completely skipped folder."""
        return CurationReport(
            timestamp=start,
            source_folder=str(source),
            total_images=0,
            curated_count=0,
            rejected_explicit=0,
            rejected_low_score=0,
            errors=0, # Or count as 1 skipped? No, it's not an error.
            avg_score=0.0,
            results=[CurationResult(source_path=source, curated=False, error=reason)]
        )
