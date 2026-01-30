"""Storage manager for TTS artifacts."""

import hashlib
import json
from pathlib import Path
from typing import Any, Dict


class StorageManager:
    """Manages artifact storage with content-based hashing."""

    def __init__(self, base_dir: Path = Path("data/audio")):
        """Initialize storage manager.

        Args:
            base_dir: Base directory for storing artifacts
        """
        self.base_dir = base_dir

    def get_content_hash(self, text: str) -> str:
        """Generate SHA-256 hash of normalized text.

        Args:
            text: Input text to hash

        Returns:
            First 12 characters of SHA-256 hash
        """
        normalized = text.strip().lower()
        hash_obj = hashlib.sha256(normalized.encode("utf-8"))
        return hash_obj.hexdigest()[:12]

    def get_artifact_dir(self, text: str) -> Path:
        """Get or create directory for text artifacts.

        Args:
            text: Input text to determine directory

        Returns:
            Path to artifact directory
        """
        content_hash = self.get_content_hash(text)
        artifact_dir = self.base_dir / content_hash
        artifact_dir.mkdir(parents=True, exist_ok=True)
        return artifact_dir

    def save_metadata(
        self, artifact_dir: Path, config: Dict[str, Any], stats: Dict[str, Any]
    ) -> Path:
        """Save generation metadata for reproducibility.

        Args:
            artifact_dir: Directory to save metadata in
            config: Configuration used for generation
            stats: Statistics from generation process

        Returns:
            Path to saved metadata file
        """
        metadata = {"config": config, "stats": stats}

        metadata_path = artifact_dir / "metadata.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        return metadata_path
