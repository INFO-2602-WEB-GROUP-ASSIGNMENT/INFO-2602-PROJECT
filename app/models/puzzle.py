from typing import Optional
from datetime import date,datetime,timezone
from sqlmodel import SQLModel, Field


class DailyPuzzle(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    puzzle_date: date = Field(index=True, unique=True)
    secret_number: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    

