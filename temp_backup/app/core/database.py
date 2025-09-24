"""
데이터베이스 연결 및 의존성 주입
"""

from typing import Generator
from sqlalchemy.orm import Session
from database.database import SessionLocal, init_database as db_init, check_database_health as db_health


def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성 주입
    FastAPI 의존성으로 사용
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_database():
    """데이터베이스 초기화"""
    return db_init()


def check_database_health():
    """데이터베이스 상태 확인"""
    return db_health()