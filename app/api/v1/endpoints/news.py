"""
뉴스 관리 엔드포인트
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_api_call
from database.models import User

router = APIRouter()

@router.get("/", summary="뉴스 목록 조회")
@log_api_call
async def get_news(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """뉴스 목록 조회 (구현 예정)"""
    return {"message": "뉴스 목록 조회 - 구현 예정"}