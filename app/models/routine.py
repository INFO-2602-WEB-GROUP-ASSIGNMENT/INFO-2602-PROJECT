from sqlmodel import SQLModel, Field
from typing import Optional

class Routine(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    user_id: int = Field(foreign_key="user.id")
    description: Optional[str] = None
    difficulty: Optional[str] = None


class RoutineExercise(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    routine_id: int = Field(foreign_key="routine.id") # Unless I'm misunderstanding, should this be foreign key to Routine.id? And shouldn't it be optional? Since exercises can exist without being in a routine? "Routine" doesn't have a "RoutineExercise" attributes, so it doesn't seem like a one-to-many relationship. Maybe this should be a many-to-many relationship?

    # from the wger API
    exercise_api_id: int
    exercise_name: str

    sets: Optional[int] = None
    reps: Optional[int] = None