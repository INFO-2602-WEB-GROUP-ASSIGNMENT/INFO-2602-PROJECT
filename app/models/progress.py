from datetime import date, datetime
from sqlmodel import SQLModel, Field
from typing import Optional
from sqlalchemy import UniqueConstraint


class ProgressLog(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "log_date", name="uq_user_log_date"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    log_date: date = Field(index=True)
    day_index: int = Field(index=True)
    routine_id: Optional[int] = Field(default=None, foreign_key="routine.id")
    payload: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
