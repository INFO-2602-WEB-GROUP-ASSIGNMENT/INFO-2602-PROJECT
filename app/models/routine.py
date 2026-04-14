from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy import UniqueConstraint

from app.models.workout_routine import RoutineWorkout

if TYPE_CHECKING:
    from app.models.workout import Workout
    from app.models.routine_exercise import RoutineExercise


class Routine(SQLModel, table=True):
    # A user creates routine scheduled for a specific day of the week. A routine can have multiple workouts and exercises assigned to it. The routine is the main user created entity in the app and serves as the model for the user's workouts and exercises.
    # created when the user creates or edits a routine
    # stores user created routine data, links to workouts, and exercise rows

    __table_args__ = (
        UniqueConstraint("user_id", "day_of_week", name="uq_user_day_of_week"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: int = Field(foreign_key="user.id")
    day_of_week: str
    description: Optional[str] = None
    workouts: list["Workout"] = Relationship(back_populates="routines", link_model=RoutineWorkout) # added back_populates to establish bidirectional relationship with Workout
    exercises: list["RoutineExercise"] = Relationship(back_populates="routine")