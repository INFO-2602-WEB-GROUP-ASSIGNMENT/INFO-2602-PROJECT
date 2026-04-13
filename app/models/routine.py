from sqlmodel import SQLModel, Field
from typing import Optional
from sqlalchemy import UniqueConstraint


class Routine(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "day_of_week", name="uq_user_day_of_week"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: int = Field(foreign_key="user.id")
    day_of_week: str
    description: Optional[str] = None