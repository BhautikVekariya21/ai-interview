from pydantic import BaseModel
from typing import Optional

class CoverLetterResponse(BaseModel):
    success: bool
    cover_letter: str
    message: Optional[str] = None
