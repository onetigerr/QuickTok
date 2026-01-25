from pathlib import Path
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from typing import List, Union
import asyncio
import os

from src.curation.models import ImageScore
from src.curation.thumbnail import ThumbnailGenerator
from src.curation.prompts import SCORING_PROMPT_SYSTEM, BatchImageScores

class ImageScorer:
    """Scores images using Groq Vision API."""
    
    def __init__(
        self, 
        model: str = "meta-llama/llama-4-maverick-17b-128e-instruct",
        api_key: str | None = None
    ):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set")
            
        self.llm = ChatGroq(
            model=model, 
            temperature=0,
            api_key=self.api_key,
            max_retries=3
        )
        self.thumbnail_gen = ThumbnailGenerator()
        self.parser = JsonOutputParser(pydantic_object=ImageScore)
        self.batch_parser = JsonOutputParser(pydantic_object=BatchImageScores)

    async def score(self, image_path: Path) -> ImageScore:
        """Score a single image."""
        base64_image = self.thumbnail_gen.to_base64(image_path)
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": SCORING_PROMPT_SYSTEM},
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}
                }
            ]
        )
        
        try:
            response = await self.llm.ainvoke([message])
            # Parse response -> returns dict
            data = self.parser.parse(response.content)
            return ImageScore(**data)
        except Exception as e:
            raise RuntimeError(f"Scoring failed for {image_path.name}: {e}")

    async def score_batch(self, image_paths: List[Path]) -> List[ImageScore]:
        """Score multiple images in one request."""
        if not image_paths:
            return []
            
        # Prepare content blocks
        content = [{"type": "text", "text": SCORING_PROMPT_SYSTEM}]
        
        for path in image_paths:
            base64_img = self.thumbnail_gen.to_base64(path)
            content.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{base64_img}"}
            })
            
        message = HumanMessage(content=content)
        
        try:
            response = await self.llm.ainvoke([message])
            parsed = self.batch_parser.parse(response.content)
            
            # Ensure we got expected number of scores
            if len(parsed['scores']) != len(image_paths):
                # Fallback or strict error? 
                # Strict error is safer to detect misalignment
                raise ValueError(f"Batch mismatch: sent {len(image_paths)}, got {len(parsed['scores'])}")
                
            # Convert dicts back to ImageScore objects if parser returned dicts
            results = []
            for item in parsed['scores']:
                if isinstance(item, ImageScore):
                    results.append(item)
                else:
                    results.append(ImageScore(**item))
            return results
            
        except Exception as e:
            # Fallback strategy: if batch fails, try sequential?
            # For now, just raise
            raise RuntimeError(f"Batch scoring failed: {e}")
