from pydantic import BaseModel
from typing import Literal

class KnowledgeAnswer(BaseModel):
    answer: str
    source_documents: list[str]
    confidence: Literal["high", "medium", "low"]

class CuratorFlag(BaseModel):
    issue_found: bool
    reasoning: str
    proposed_update: str
