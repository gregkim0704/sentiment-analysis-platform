"""
알림 관리 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List
from datetime import datetime
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_api_call
from database.models import User

router = APIRouter()

@router.patch("/{alert_id}/dismiss", summary="알림 해제")
@log_api_call
async def dismiss_alert(
    alert_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """알림 해제 (구현 예정)"""
    
    # 임시로 성공 응답 반환
    # TODO: 실제 알림 시스템 구현 후 업데이트
    return {"message": "알림이 해제되었습니다.", "alert_id": alert_id}

@router.get("/", summary="알림 목록 조회")
@log_api_call
async def get_alerts(
    company_id: int = None,
    is_active: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """알림 목록 조회 (구현 예정)"""
    
    # 임시로 빈 배열 반환
    # TODO: 실제 알림 시스템 구현 후 업데이트
    return []