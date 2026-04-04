from sqlmodel import Session, select
from app.models.game_session import GameSession


class GameSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, session: GameSession) -> GameSession:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def update(self, session: GameSession) -> GameSession:
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def get_by_id(self, session_id: int):
        return self.db.get(GameSession, session_id)

    def get_user_session_for_puzzle(self, user_id: int, puzzle_id: int):
        statement = select(GameSession).where(
            GameSession.user_id == user_id,
            GameSession.puzzle_id == puzzle_id
        )
        return self.db.exec(statement).first()

    def get_sessions_by_user(self, user_id: int):
        statement = select(GameSession).where(GameSession.user_id == user_id)
        return self.db.exec(statement).all()