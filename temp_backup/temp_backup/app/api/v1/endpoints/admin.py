"""
관리자 엔드포인트
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import require_admin
from app.core.logging import log_api_call
from database.models import User

router = APIRouter()

@router.get("/system-info", summary="시스템 정보")
@log_api_call
async def get_system_info(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """시스템 정보 조회 (구현 예정)"""
    return {"message": "시스템 정보 - 구현 예정"}