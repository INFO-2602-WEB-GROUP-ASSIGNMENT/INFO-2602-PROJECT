from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from app.models.workout_routine import RoutineWorkout

if TYPE_CHECKING: # type checking to avoid circular imports
    from app.models.routine import Routine


class Workout(SQLModel, table=True):
    # API exercise record used by the app as a workout entry
    # Populated from the exercise API and linked to routines through the bridge table
    # Stores exercise data, not user created data. That's what the RoutineExercise table is for
    

    id: Optional[int] =  Field(default = None, primary_key = True)
    name: str
    category: str
    user_id: int = Field(foreign_key="user.id")
    description: Optional[str] = None
    routines: list["Routine"] = Relationship(back_populates="workouts", link_model=RoutineWorkout) # added back_populates to establish bidirectional relationship with Routine
    
    