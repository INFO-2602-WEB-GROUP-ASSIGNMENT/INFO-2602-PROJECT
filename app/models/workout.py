from sqlmodel import SQLModel, Field
from typing import Optional

class Workout(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    category: str
    difficulty: str