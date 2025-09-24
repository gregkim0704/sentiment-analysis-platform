"""
사용자 관리 엔드포인트
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.database import get_db
from app.core.security import get_current_user, require_admin, require_analyst_or_admin
from app.core.logging import logger, log_api_call
from app.schemas.user import (
    UserResponse, 
    UserCreate, 
    UserUpdate, 
    UserListResponse,
    UserWithStats,
    UserStats
)
from app.schemas.base import PaginationSchema, ResponseSchema
from database.models import User, UserRole, AnalysisRequest, AlertRule

router = APIRouter()


@router.get("/", response_model=UserListResponse, summary="사용자 목록 조회")
@log_api_call
async def get_users(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    search: Optional[str] = Query(None, description="검색어 (이름 또는 이메일)"),
    role: Optional[UserRole] = Query(None, description="역할 필터"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    current_user: User = Depends(require_analyst_or_admin),
    db: Session = Depends(get_db)
):
    """
    사용자 목록 조회 (분석가 이상 권한 필요)
    
    - **page**: 페이지 번호
    - **size**: 페이지 크기
    - **search**: 검색어 (이름 또는 이메일)
    - **role**: 역할 필터
    - **is_active**: 활성 상태 필터
    """
    query = db.query(User)
    
    # 검색 필터
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (User.full_name.ilike(search_filter)) |
            (User.email.ilike(search_filter))
        )
    
    # 역할 필터
    if role:
        query = query.filter(User.role == role)
    
    # 활성 상태 필터
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    # 전체 개수 조회
    total = query.count()
    
    # 페이지네이션 적용
    offset = (page - 1) * size
    users = query.offset(offset).limit(size).all()
    
    logger.info(f"사용자 목록 조회: {len(users)}개 (전체 {total}개)")
    
    return UserListResponse(
        users=[UserResponse.from_orm(user) for user in users],
        total=total,
        page=page,
        size=size
    )


@router.get("/me", response_model=UserResponse, summary="내 정보 조회")
@log_api_call
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """현재 로그인한 사용자의 정보 조회"""
    return UserResponse.from_orm(current_user)


@router.get("/{user_id}", response_model=UserWithStats, summary="사용자 상세 조회")
@log_api_call
async def get_user(
    user_id: int,
    current_user: User = Depends(require_analyst_or_admin),
    db: Session = Depends(get_db)
):
    """
    특정 사용자 상세 정보 조회 (분석가 이상 권한 필요)
    
    - **user_id**: 조회할 사용자 ID
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 사용자 통계 조회
    total_analysis_requests = db.query(func.count(AnalysisRequest.id)).filter(
        AnalysisRequest.user_id == user_id
    ).scalar() or 0
    
    active_alerts = db.query(func.count(AlertRule.id)).filter(
        AlertRule.user_id == user_id,
        AlertRule.is_active == True
    ).scalar() or 0
    
    # 마지막 분석 요청 시간
    last_analysis = db.query(func.max(AnalysisRequest.created_at)).filter(
        AnalysisRequest.user_id == user_id
    ).scalar()
    
    stats = UserStats(
        total_analysis_requests=total_analysis_requests,
        active_alerts=active_alerts,
        last_activity=last_analysis or user.last_login
    )
    
    logger.info(f"사용자 상세 조회: {user.email}")
    
    return UserWithStats(
        **UserResponse.from_orm(user).dict(),
        stats=stats
    )


@router.post("/", response_model=UserResponse, summary="사용자 생성")
@log_api_call
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    새 사용자 생성 (관리자 권한 필요)
    
    - **email**: 이메일 주소 (고유해야 함)
    - **password**: 비밀번호
    - **full_name**: 전체 이름
    - **role**: 사용자 역할
    """
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일 주소입니다"
        )
    
    # 비밀번호 해시 생성
    from app.core.security import create_password_hash
    
    # 새 사용자 생성
    user = User(
        email=user_data.email,
        password_hash=create_password_hash(user_data.password),
        full_name=user_data.full_name,
        role=user_data.role,
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"새 사용자 생성: {user.email} (생성자: {current_user.email})")
    
    return UserResponse.from_orm(user)


@router.put("/{user_id}", response_model=UserResponse, summary="사용자 정보 수정")
@log_api_call
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    사용자 정보 수정 (관리자 권한 필요)
    
    - **user_id**: 수정할 사용자 ID
    - **full_name**: 전체 이름 (선택)
    - **role**: 사용자 역할 (선택)
    - **is_active**: 활성 상태 (선택)
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 자기 자신의 역할은 변경할 수 없음
    if user_id == current_user.id and user_data.role is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 역할은 변경할 수 없습니다"
        )
    
    # 업데이트할 필드만 수정
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"사용자 정보 수정: {user.email} (수정자: {current_user.email})")
    
    return UserResponse.from_orm(user)


@router.delete("/{user_id}", response_model=ResponseSchema, summary="사용자 삭제")
@log_api_call
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    사용자 삭제 (관리자 권한 필요)
    
    - **user_id**: 삭제할 사용자 ID
    
    실제로는 비활성화 처리됩니다.
    """
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="사용자를 찾을 수 없습니다"
        )
    
    # 자기 자신은 삭제할 수 없음
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="자신의 계정은 삭제할 수 없습니다"
        )
    
    # 실제 삭제 대신 비활성화
    user.is_active = False
    db.commit()
    
    logger.info(f"사용자 비활성화: {user.email} (처리자: {current_user.email})")
    
    return ResponseSchema(
        success=True,
        message="사용자가 비활성화되었습니다"
    )


@router.get("/stats/summary", response_model=dict, summary="사용자 통계 요약")
@log_api_call
async def get_user_stats_summary(
    current_user: User = Depends(require_analyst_or_admin),
    db: Session = Depends(get_db)
):
    """
    사용자 통계 요약 (분석가 이상 권한 필요)
    """
    # 전체 사용자 수
    total_users = db.query(func.count(User.id)).scalar()
    
    # 활성 사용자 수
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    
    # 역할별 사용자 수
    role_stats = {}
    for role in UserRole:
        count = db.query(func.count(User.id)).filter(User.role == role).scalar()
        role_stats[role.value] = count
    
    # 최근 가입자 수 (30일)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_users = db.query(func.count(User.id)).filter(
        User.created_at >= thirty_days_ago
    ).scalar()
    
    logger.info("사용자 통계 요약 조회")
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "inactive_users": total_users - active_users,
        "role_distribution": role_stats,
        "recent_registrations": recent_users
    }