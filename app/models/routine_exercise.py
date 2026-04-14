from typing import List, Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.routine import Routine


class RoutineExercise(SQLModel, table=True):
    # assigns exercises to routines.
    # Populated when a routine is created, edited, or remixed. It stores the selected exercise from the API, the planned sets and reps for the user.
    
    id: Optional[int] = Field(default=None, primary_key=True)
    routine_id: int = Field(foreign_key="routine.id")
    exercise_api_id: int
    exercise_name: str
    sets: Optional[int] = None
    reps: Optional[int] = None
    routine: Optional["Routine"] = Relationship(back_populates="exercises")

class RoutineExerciseCreate(SQLModel):
    # Model payload for adding an exercise to a routine
    # Populated from user input. It stores the API exercise id, planned sets and reps before the row is written to the database.
    
    exercise_id: int
    sets: Optional[int] = 3
    reps: Optional[int] = 10


class RoutineCreate(SQLModel):
    # Model payload for creating a routine
    # Populated from user input when a routine is created. The exercises inside this payload reference API exercises and planned data.
    
    day_of_week: str
    description: Optional[str] = None
    exercises: List[RoutineExerciseCreate] = []


class RoutineUpdate(SQLModel):
    # Model payload for updating routine metadata
    # Populated from user input when editing an existing routine
    
    description: Optional[str] = None