from pydantic import BaseModel
from typing import List, Optional

class Step(BaseModel):
    title: str
    description: str
    commands: Optional[str] = ""
    language: Optional[str] = "bash"

class WriteupContext(BaseModel):
    title: str
    category: str
    difficulty: str
    flag: str
    description: str
    link: Optional[str] = ""
    team: str
    date: str
    steps: List[Step] = []
