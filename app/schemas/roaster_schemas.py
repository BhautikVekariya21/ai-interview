from typing import List
from pydantic import BaseModel

class RoastResponse(BaseModel):
    success: bool
    score: int
    strengths: List[str]
    weaknesses: List[str]
    brutal_roast: str
