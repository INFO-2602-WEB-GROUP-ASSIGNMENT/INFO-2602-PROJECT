from typing import Optional
from datetime import datetime,timezone
from sqlmodel import SQLModel, Field


class GameSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    puzzle_id: int = Field(foreign_key="dailypuzzle.id")
    status: str = Field(default="active")
    attempts_used: int = Field(default=0)
    max_attempts: int = Field(default=7)
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None