from sqlmodel import SQLModel, Field
from typing import Optional, List

class RoutineExercise(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    routine_id: int = Field(foreign_key="routine.id")
    exercise_api_id: int
    exercise_name: str
    sets: Optional[int] = None
    reps: Optional[int] = None

class RoutineExerciseCreate(SQLModel):
    exercise_id: int
    sets: Optional[int] = 3
    reps: Optional[int] = 10


class RoutineCreate(SQLModel):
    day_of_week: str
    description: Optional[str] = None
    exercises: List[RoutineExerciseCreate] = []


class RoutineUpdate(SQLModel):
    description: Optional[str] = None