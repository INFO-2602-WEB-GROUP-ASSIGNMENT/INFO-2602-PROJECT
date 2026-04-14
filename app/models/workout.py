from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from app.models.workout_routine import WorkoutRoutine

if TYPE_CHECKING: # type checking to avoid circular imports
    from app.models.routine import Routine

class Workout(SQLModel, table=True):
    id: Optional[int] =  Field(default = None, primary_key = True)
    name: str
    category: str
    user_id: int = Field(foreign_key="user.id")
    description: Optional[str] = None
    routines: list["Routine"] = Relationship(back_populates="workouts", link_model=WorkoutRoutine) # added back_populates to establish bidirectional relationship with Routine
    
    