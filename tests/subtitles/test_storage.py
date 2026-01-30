"""Tests for storage manager."""

import pytest
from pathlib import Path
import tempfile
import json

from src.subtitles.storage import StorageManager


def test_content_hash():
    """Test content hash generation."""
    storage = StorageManager()

    # Same text should produce same hash
    hash1 = storage.get_content_hash("Hello world")
    hash2 = storage.get_content_hash("Hello world")
    assert hash1 == hash2

    # Different text should produce different hash
    hash3 = storage.get_content_hash("Different text")
    assert hash1 != hash3

    # Case-insensitive
    hash4 = storage.get_content_hash("HELLO WORLD")
    assert hash1 == hash4


def test_artifact_dir_creation():
    """Test artifact directory creation."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = StorageManager(base_dir=Path(tmpdir))

        artifact_dir = storage.get_artifact_dir("Test text")

        assert artifact_dir.exists()
        assert artifact_dir.is_dir()
        assert artifact_dir.parent == Path(tmpdir)


def test_save_metadata():
    """Test metadata saving."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = StorageManager(base_dir=Path(tmpdir))

        artifact_dir = storage.get_artifact_dir("Test")

        config = {"language": "es-ES", "voice": "test"}
        stats = {"word_count": 10, "duration_ms": 5000}

        metadata_path = storage.save_metadata(artifact_dir, config, stats)

        assert metadata_path.exists()

        # Verify content
        with open(metadata_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["config"] == config
        assert data["stats"] == stats


def test_hash_length():
    """Test that hash is correct length."""
    storage = StorageManager()
    hash_value = storage.get_content_hash("Test")
    assert len(hash_value) == 12
