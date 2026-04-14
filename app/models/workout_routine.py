from sqlmodel import SQLModel, Field
from typing import Optional

# each workoutroutine links a routine to a workout, allowing users to associate specific workouts with their routines. WorkoutRoutine is a bridge table that enables a many-to-many relationship between routines and workouts, allowing users to have multiple workouts in a routine and the same workout to be part of multiple routines.
class WorkoutRoutine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    routine_id: int = Field(foreign_key="routine.id")
    workout_id: int = Field(foreign_key="workout.id")