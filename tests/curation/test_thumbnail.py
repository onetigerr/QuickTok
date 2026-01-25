import pytest
from pathlib import Path
from PIL import Image
import io
import base64
from src.curation.thumbnail import ThumbnailGenerator

@pytest.fixture
def sample_image(tmp_path):
    """Creates a large sample image for testing."""
    img_path = tmp_path / "test_large.jpg"
    # Create 1000x1000 red image
    img = Image.new('RGB', (1000, 1000), color='red')
    img.save(img_path)
    return img_path

@pytest.fixture
def png_image(tmp_path):
    """Creates a PNG image with transparency."""
    img_path = tmp_path / "test_transparent.png"
    img = Image.new('RGBA', (800, 800), color=(0, 255, 0, 128))
    img.save(img_path)
    return img_path

def test_resize_constraint(sample_image):
    generator = ThumbnailGenerator(max_size=(512, 512))
    thumbnail_bytes = generator.generate(sample_image)
    
    with Image.open(io.BytesIO(thumbnail_bytes)) as img:
        assert img.width <= 512
        assert img.height <= 512
        assert img.format == "JPEG"

def test_file_size_compression(sample_image):
    generator = ThumbnailGenerator(quality=60)
    thumbnail_bytes = generator.generate(sample_image)
    
    # Original 1000x1000 red image is small due to solid color, 
    # but let's check it's a valid jpeg byte stream
    assert len(thumbnail_bytes) > 0
    assert thumbnail_bytes.startswith(b'\xff\xd8')  # JPEG signature

def test_png_automation_conversion(png_image):
    """Test that PNGs are converted to JPEG RGB automatically."""
    generator = ThumbnailGenerator()
    thumbnail_bytes = generator.generate(png_image)
    
    with Image.open(io.BytesIO(thumbnail_bytes)) as img:
        assert img.format == "JPEG"
        assert img.mode == "RGB"

def test_base64_output(sample_image):
    generator = ThumbnailGenerator()
    b64_str = generator.to_base64(sample_image)
    
    assert isinstance(b64_str, str)
    # Validate it decodes back
    decoded = base64.b64decode(b64_str)
    assert decoded.startswith(b'\xff\xd8')

def test_token_estimation(sample_image):
    generator = ThumbnailGenerator()
    tokens = generator.estimate_tokens(sample_image)
    # 512*512 / 750 approx 349
    assert 300 < tokens < 400
