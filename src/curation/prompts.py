from pydantic import BaseModel
from typing import List
from src.curation.models import ImageScore


class BatchImageScores(BaseModel):
    scores: List[ImageScore]


with(open("data/prompts/scoring_system.txt") as stream):
    SCORING_PROMPT_SYSTEM = stream.read()

