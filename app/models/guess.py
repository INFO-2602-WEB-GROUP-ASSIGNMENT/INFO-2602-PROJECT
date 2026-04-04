from typing import Optional
from datetime import datetime,timezone
from sqlmodel import SQLModel, Field


class Guess(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="gamesession.id")
    guess_value: str
    bulls: int
    cows: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))