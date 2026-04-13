from sqlmodel import SQLModel, Field
from typing import Optional

class WorkoutRoutine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    routine_id: int = Field(foreign_key="routine.id")
    workout_id: int = Field(foreign_key="workout.id")