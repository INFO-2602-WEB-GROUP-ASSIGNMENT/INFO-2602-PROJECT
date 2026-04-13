from sqlmodel import SQLModel, Field
from typing import Optional

class Workout(SQLModel, table=True):
    id: Optional[int] =  Field(default = None, primary_key = True)
    name: str
    category: str
    user_id: int = Field(foreign_key="user.id")
    description: Optional[str] = None