from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint

from app.models.workout_routine import WorkoutRoutine

if TYPE_CHECKING:
    from app.models.workout import Workout


class Routine(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "day_of_week", name="uq_user_day_of_week"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: int = Field(foreign_key="user.id")
    day_of_week: str
    description: Optional[str] = None
    workouts: list["Workout"] = Relationship(back_populates="routines", link_model=WorkoutRoutine) # added back_populates to establish bidirectional relationship with Workout