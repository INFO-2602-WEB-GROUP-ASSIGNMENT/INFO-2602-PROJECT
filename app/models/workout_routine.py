from typing import ClassVar, Optional

from sqlmodel import SQLModel, Field


class RoutineWorkout(SQLModel, table=True):
    # Join table linking routines to workouts.
    # Populated whenever a user associates an API exercise/workout entry with a routine
    # Stores only foreign keys to the routine and workout tables, no user created data. That's what the RoutineExercise table is for

    id: Optional[int] = Field(default=None, primary_key=True)
    routine_id: int = Field(foreign_key="routine.id")
    workout_id: int = Field(foreign_key="workout.id")