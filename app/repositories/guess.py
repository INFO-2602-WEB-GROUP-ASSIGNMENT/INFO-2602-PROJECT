from sqlmodel import Session, select
from app.models.guess import Guess


class GuessRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, guess: Guess) -> Guess:
        self.db.add(guess)
        self.db.commit()
        self.db.refresh(guess)
        return guess

    def get_by_session(self, session_id: int):
        statement = select(Guess).where(Guess.session_id == session_id)
        return self.db.exec(statement).all()