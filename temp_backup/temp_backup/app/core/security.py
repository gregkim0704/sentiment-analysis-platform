"""
보안 관련 유틸리티
"""

from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from database.models import User


# 비밀번호 해싱 컨텍스트
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT 토큰 스키마
security = HTTPBearer()


def create_password_hash(password: str) -> str:
    """비밀번호 해시 생성"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """비밀번호 검증"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    subject: Union[str, Any], 
    expires_delta: timedelta = None
) -> str:
    """액세스 토큰 생성"""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET_KEY, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(subject: Union[str, Any]) -> str:
    """리프레시 토큰 생성"""
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> Optional[str]:
    """토큰 검증 및 사용자 ID 반환"""
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError as e:
        logger.warning(f"JWT 토큰 검증 실패: {e}")
        return None


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """현재 사용자 조회"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # 토큰에서 사용자 ID 추출
        user_id = verify_token(credentials.credentials)
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # 데이터베이스에서 사용자 조회
    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise credentials_exception
    
    # 사용자 활성 상태 확인
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 사용자입니다"
        )
    
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """현재 활성 사용자 조회"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 사용자입니다"
        )
    return current_user


def require_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """관리자 권한 필요"""
    from database.models import UserRole
    
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다"
        )
    return current_user


def require_analyst_or_admin(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """분석가 또는 관리자 권한 필요"""
    from database.models import UserRole
    
    if current_user.role not in [UserRole.ANALYST, UserRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="분석가 또는 관리자 권한이 필요합니다"
        )
    return current_user


class RateLimiter:
    """속도 제한기"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def is_allowed(
        self, 
        key: str, 
        limit: int, 
        window: int = 60
    ) -> tuple[bool, dict]:
        """
        속도 제한 확인
        
        Args:
            key: 제한 키 (예: user_id, ip_address)
            limit: 제한 횟수
            window: 시간 윈도우 (초)
        
        Returns:
            (허용 여부, 상태 정보)
        """
        current_count = self.redis.get(key) or 0
        
        if current_count >= limit:
            return False, {
                "allowed": False,
                "limit": limit,
                "remaining": 0,
                "reset_time": window
            }
        
        # 카운터 증가
        new_count = self.redis.increment(key)
        
        # 첫 번째 요청인 경우 TTL 설정
        if new_count == 1:
            self.redis.expire(key, window)
        
        return True, {
            "allowed": True,
            "limit": limit,
            "remaining": limit - new_count,
            "reset_time": window
        }


def generate_api_key() -> str:
    """API 키 생성"""
    import secrets
    return secrets.token_urlsafe(32)


def hash_api_key(api_key: str) -> str:
    """API 키 해시"""
    return pwd_context.hash(api_key)


def verify_api_key(plain_key: str, hashed_key: str) -> bool:
    """API 키 검증"""
    return pwd_context.verify(plain_key, hashed_key)


def sanitize_input(text: str) -> str:
    """입력 데이터 정제"""
    import html
    import re
    
    # HTML 이스케이프
    text = html.escape(text)
    
    # 특수 문자 제거 (필요에 따라 조정)
    text = re.sub(r'[<>"\']', '', text)
    
    # 연속된 공백 제거
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text


def validate_email(email: str) -> bool:
    """이메일 형식 검증"""
    import re
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def generate_secure_filename(filename: str) -> str:
    """안전한 파일명 생성"""
    import os
    import uuid
    from werkzeug.utils import secure_filename
    
    # 파일 확장자 추출
    name, ext = os.path.splitext(filename)
    
    # 안전한 파일명 생성
    safe_name = secure_filename(name)
    
    # UUID 추가로 중복 방지
    unique_name = f"{safe_name}_{uuid.uuid4().hex[:8]}{ext}"
    
    return unique_name