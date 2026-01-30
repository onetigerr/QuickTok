from pathlib import Path
from PIL import Image
import base64
import io

class ThumbnailGenerator:
    """Optimizes images for LLM consumption (resize, compress, encode)."""
    
    def __init__(
        self, 
        max_size: tuple[int, int] = (512, 512),
        quality: int = 60,
        format: str = "JPEG"
    ):
        self.max_size = max_size
        self.quality = quality
        self.format = format
    
    def generate(self, image_path: Path) -> bytes:
        """
        Creates an optimized thumbnail.
        - Resizes maintaining aspect ratio (LANCZOS)
        - Compresses to specified quality
        - Returns bytes
        """
        img_copy = None
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed (handles RGBA, P, etc. for JPEG)
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                
                # Copy execution to avoid modifying original if we were returning the object
                # (though here we just save to bytes)
                img_copy = img.copy()
                
            # Process outside the with block to ensure original is closed
            # Resize if larger than max_size
            img_copy.thumbnail(self.max_size, Image.Resampling.LANCZOS)
            
            # Compress to bytes
            buffer = io.BytesIO()
            img_copy.save(
                buffer, 
                format=self.format, 
                quality=self.quality, 
                optimize=True
            )
            return buffer.getvalue()
        except OSError as e:
            # Re-raise with context if file issues
            raise OSError(f"Failed to process image {image_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"Thumbnail generation failed for {image_path}: {e}")
        finally:
            # Explicitly close the copy to release resources
            if img_copy is not None:
                img_copy.close()

    def to_base64(self, image_path: Path) -> str:
        """Returns base64-encoded string for API usage."""
        thumbnail_bytes = self.generate(image_path)
        return base64.b64encode(thumbnail_bytes).decode("utf-8")
    
    def estimate_tokens(self, image_path: Path) -> int:
        """
        Estimates token usage for the vision model.
        Approximation: (width * height) / 750 for standard vision models.
        """
        thumbnail_bytes = self.generate(image_path)
        buffer = io.BytesIO(thumbnail_bytes)
        try:
            with Image.open(buffer) as img:
                return int((img.width * img.height) / 750)
        finally:
            buffer.close()

