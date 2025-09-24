"""
사용자 관련 스키마
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, field_validator
from database.models import UserRole
from app.schemas.base import BaseSchema


class UserBase(BaseSchema):
    """사용자 기본 스키마"""
    
    email: EmailStr = Field(..., description="이메일 주소")
    full_name: str = Field(..., min_length=2, max_length=100, description="전체 이름")
    role: UserRole = Field(UserRole.VIEWER, description="사용자 역할")


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다')
        
        # 비밀번호 복잡성 검증
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('비밀번호는 대문자, 소문자, 숫자를 포함해야 합니다')
        
        return v


class UserUpdate(BaseSchema):
    """사용자 수정 스키마"""
    
    full_name: Optional[str] = Field(None, min_length=2, max_length=100, description="전체 이름")
    role: Optional[UserRole] = Field(None, description="사용자 역할")
    is_active: Optional[bool] = Field(None, description="활성 상태")


class UserPasswordUpdate(BaseSchema):
    """비밀번호 변경 스키마"""
    
    current_password: str = Field(..., description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, max_length=100, description="새 비밀번호")
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('새 비밀번호는 최소 8자 이상이어야 합니다')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('새 비밀번호는 대문자, 소문자, 숫자를 포함해야 합니다')
        
        return v


class UserResponse(UserBase):
    """사용자 응답 스키마"""
    
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None


class UserListResponse(BaseSchema):
    """사용자 목록 응답 스키마"""
    
    users: List[UserResponse]
    total: int
    page: int
    size: int


class UserProfile(UserResponse):
    """사용자 프로필 스키마"""
    
    # 추가 프로필 정보가 필요한 경우 여기에 추가
    pass


class UserStats(BaseSchema):
    """사용자 통계 스키마"""
    
    total_analysis_requests: int = Field(0, description="총 분석 요청 수")
    active_alerts: int = Field(0, description="활성 알림 수")
    last_activity: Optional[datetime] = Field(None, description="마지막 활동 시간")


class UserWithStats(UserResponse):
    """통계 포함 사용자 스키마"""
    
    stats: UserStats