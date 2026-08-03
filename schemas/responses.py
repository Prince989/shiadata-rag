from pydantic import BaseModel
from typing import List, Optional

class SourceNode(BaseModel):
    book: str
    chapter: str
    footnotes: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceNode]
    language_detected: Optional[str] = "unknown"