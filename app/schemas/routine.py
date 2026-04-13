from sqlmodel import SQLModel
from typing import Optional, List


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


class RoutineExerciseRemix(SQLModel):
    replacement_exercise_id: int
    replacement_name: str