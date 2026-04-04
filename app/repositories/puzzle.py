from datetime import date
from sqlmodel import Session, select
from app.models.puzzle import DailyPuzzle


class DailyPuzzleRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, puzzle: DailyPuzzle) -> DailyPuzzle:
        self.db.add(puzzle)
        self.db.commit()
        self.db.refresh(puzzle)
        return puzzle

    def get_by_date(self, puzzle_date: date):
        statement = select(DailyPuzzle).where(DailyPuzzle.puzzle_date == puzzle_date)
        return self.db.exec(statement).first()

    def get_by_id(self, puzzle_id: int):
        return self.db.get(DailyPuzzle, puzzle_id)