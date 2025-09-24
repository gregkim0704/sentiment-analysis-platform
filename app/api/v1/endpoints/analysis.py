"""
분석 요청 엔드포인트
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_api_call
from database.models import User

router = APIRouter()

@router.post("/request", summary="분석 요청")
@log_api_call
async def create_analysis_request(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """분석 요청 생성 (구현 예정)"""
    return {"message": "분석 요청 생성 - 구현 예정"}