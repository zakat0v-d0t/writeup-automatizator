from pydantic import BaseModel
from typing import List, Optional

class Step(BaseModel):
    title: str
    description: str
    commands: str = ""
    language: str = "bash"

class WriteupContext(BaseModel):
    title: str
    category: str
    difficulty: str
    flag: str
    description: str
    link: str = ""
    team: str
    date: str
    steps: List[Step] = []
