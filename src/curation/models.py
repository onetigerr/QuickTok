from pydantic import BaseModel, Field
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

class ImageScore(BaseModel):
    """Structured evaluation from LLM."""
    wow_factor: int = Field(ge=0, le=10, description="Visual appeal (1-10)")
    engagement: int = Field(ge=0, le=10, description="Potential to stop scrolling (1-10)")
    tiktok_fit: int = Field(ge=0, le=10, description="Suitability for platform (1-10)")
    is_explicit: bool = Field(description="True if NSFW/banned content")
    reasoning: str = Field(description="Brief explanation of the score")
    
    @property
    def combined_score(self) -> float:
        """Calculates average score, returns 0.0 if explicit."""
        if self.is_explicit:
            return 0.0
        return (self.wow_factor + self.engagement + self.tiktok_fit) / 3.0

class CurationConfig(BaseModel):
    """Pipeline configuration."""
    threshold: float = 7.0
    max_size: tuple[int, int] = (512, 512)
    jpeg_quality: int = 60
    batch_size: int = 5
    dry_run: bool = False

@dataclass
class CurationResult:
    """Result for a single image."""
    source_path: Path
    score: Optional[ImageScore] = None
    curated: bool = False
    error: Optional[str] = None
    destination: Optional[Path] = None

class CurationReport(BaseModel):
    """Execution summary."""
    timestamp: datetime
    source_folder: str
    total_images: int
    curated_count: int
    rejected_explicit: int
    rejected_low_score: int
    errors: int
    avg_score: float = 0.0
    results: List[CurationResult] = Field(default_factory=list)
