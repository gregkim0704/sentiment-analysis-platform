"""
인증 관련 스키마
"""

from typing import Optional
from pydantic import BaseModel, Field, EmailStr, field_validator
from app.schemas.base import BaseSchema
from app.schemas.user import UserResponse


class LoginRequest(BaseSchema):
    """로그인 요청 스키마"""
    
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=1, description="비밀번호")
    remember_me: bool = Field(False, description="로그인 상태 유지")


class LoginResponse(BaseSchema):
    """로그인 응답 스키마"""
    
    access_token: str = Field(..., description="액세스 토큰")
    refresh_token: str = Field(..., description="리프레시 토큰")
    token_type: str = Field("bearer", description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료 시간 (초)")
    user: UserResponse = Field(..., description="사용자 정보")


class RefreshTokenRequest(BaseSchema):
    """토큰 갱신 요청 스키마"""
    
    refresh_token: str = Field(..., description="리프레시 토큰")


class RefreshTokenResponse(BaseSchema):
    """토큰 갱신 응답 스키마"""
    
    access_token: str = Field(..., description="새 액세스 토큰")
    token_type: str = Field("bearer", description="토큰 타입")
    expires_in: int = Field(..., description="토큰 만료 시간 (초)")


class RegisterRequest(BaseSchema):
    """회원가입 요청 스키마"""
    
    email: EmailStr = Field(..., description="이메일 주소")
    password: str = Field(..., min_length=8, max_length=100, description="비밀번호")
    full_name: str = Field(..., min_length=2, max_length=100, description="전체 이름")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다')
        
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        
        if not (has_upper and has_lower and has_digit):
            raise ValueError('비밀번호는 대문자, 소문자, 숫자를 포함해야 합니다')
        
        return v


class RegisterResponse(BaseSchema):
    """회원가입 응답 스키마"""
    
    user: UserResponse = Field(..., description="생성된 사용자 정보")
    message: str = Field("회원가입이 완료되었습니다", description="응답 메시지")


class PasswordResetRequest(BaseSchema):
    """비밀번호 재설정 요청 스키마"""
    
    email: EmailStr = Field(..., description="이메일 주소")


class PasswordResetResponse(BaseSchema):
    """비밀번호 재설정 응답 스키마"""
    
    message: str = Field("비밀번호 재설정 이메일이 발송되었습니다", description="응답 메시지")


class PasswordResetConfirm(BaseSchema):
    """비밀번호 재설정 확인 스키마"""
    
    token: str = Field(..., description="재설정 토큰")
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


class LogoutResponse(BaseSchema):
    """로그아웃 응답 스키마"""
    
    message: str = Field("로그아웃되었습니다", description="응답 메시지")


class TokenValidationResponse(BaseSchema):
    """토큰 검증 응답 스키마"""
    
    valid: bool = Field(..., description="토큰 유효성")
    user: Optional[UserResponse] = Field(None, description="사용자 정보")
    expires_at: Optional[int] = Field(None, description="토큰 만료 시간")


class ChangePasswordRequest(BaseSchema):
    """비밀번호 변경 요청 스키마"""
    
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


class ChangePasswordResponse(BaseSchema):
    """비밀번호 변경 응답 스키마"""
    
    message: str = Field("비밀번호가 성공적으로 변경되었습니다", description="응답 메시지")