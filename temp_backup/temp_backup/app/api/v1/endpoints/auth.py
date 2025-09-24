"""
인증 관련 엔드포인트
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    verify_password, 
    create_access_token, 
    create_refresh_token,
    create_password_hash,
    get_current_user,
    verify_token
)
from app.core.config import settings
from app.core.logging import logger, log_api_call
from app.schemas.auth import (
    LoginRequest, 
    LoginResponse, 
    RegisterRequest, 
    RegisterResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    PasswordResetRequest,
    PasswordResetResponse,
    ChangePasswordRequest,
    ChangePasswordResponse,
    LogoutResponse,
    TokenValidationResponse
)
from app.schemas.user import UserResponse
from database.models import User, UserRole

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse, summary="로그인")
@log_api_call
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    사용자 로그인
    
    - **email**: 이메일 주소
    - **password**: 비밀번호
    - **remember_me**: 로그인 상태 유지 여부
    """
    # 사용자 조회
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user:
        logger.warning(f"존재하지 않는 이메일로 로그인 시도: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )
    
    # 비밀번호 검증
    if not verify_password(login_data.password, user.password_hash):
        logger.warning(f"잘못된 비밀번호로 로그인 시도: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다"
        )
    
    # 사용자 활성 상태 확인
    if not user.is_active:
        logger.warning(f"비활성 사용자 로그인 시도: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비활성화된 계정입니다"
        )
    
    # 토큰 만료 시간 설정
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    if login_data.remember_me:
        access_token_expires = timedelta(days=7)  # 로그인 유지시 7일
    
    # 토큰 생성
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(subject=user.id)
    
    # 마지막 로그인 시간 업데이트
    from datetime import datetime
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info(f"사용자 로그인 성공: {user.email}")
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds()),
        user=UserResponse.from_orm(user)
    )


@router.post("/register", response_model=RegisterResponse, summary="회원가입")
@log_api_call
async def register(
    register_data: RegisterRequest,
    db: Session = Depends(get_db)
):
    """
    새 사용자 회원가입
    
    - **email**: 이메일 주소 (고유해야 함)
    - **password**: 비밀번호 (8자 이상, 대소문자+숫자 포함)
    - **full_name**: 전체 이름
    """
    # 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == register_data.email).first()
    if existing_user:
        logger.warning(f"중복 이메일로 회원가입 시도: {register_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일 주소입니다"
        )
    
    # 새 사용자 생성
    user = User(
        email=register_data.email,
        password_hash=create_password_hash(register_data.password),
        full_name=register_data.full_name,
        role=UserRole.VIEWER,  # 기본 역할
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"새 사용자 회원가입: {user.email}")
    
    return RegisterResponse(
        user=UserResponse.from_orm(user),
        message="회원가입이 완료되었습니다"
    )


@router.post("/refresh", response_model=RefreshTokenResponse, summary="토큰 갱신")
@log_api_call
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    리프레시 토큰으로 새 액세스 토큰 발급
    
    - **refresh_token**: 리프레시 토큰
    """
    # 리프레시 토큰 검증
    user_id = verify_token(refresh_data.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 리프레시 토큰입니다"
        )
    
    # 사용자 존재 확인
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없거나 비활성 상태입니다"
        )
    
    # 새 액세스 토큰 생성
    access_token_expires = timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=user.id,
        expires_delta=access_token_expires
    )
    
    logger.info(f"토큰 갱신: {user.email}")
    
    return RefreshTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=int(access_token_expires.total_seconds())
    )


@router.post("/logout", response_model=LogoutResponse, summary="로그아웃")
@log_api_call
async def logout(
    current_user: User = Depends(get_current_user)
):
    """
    사용자 로그아웃
    
    현재는 클라이언트 측에서 토큰을 삭제하도록 안내
    향후 토큰 블랙리스트 기능 추가 예정
    """
    logger.info(f"사용자 로그아웃: {current_user.email}")
    
    return LogoutResponse(
        message="로그아웃되었습니다. 클라이언트에서 토큰을 삭제해주세요."
    )


@router.post("/change-password", response_model=ChangePasswordResponse, summary="비밀번호 변경")
@log_api_call
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    현재 사용자의 비밀번호 변경
    
    - **current_password**: 현재 비밀번호
    - **new_password**: 새 비밀번호
    """
    # 현재 비밀번호 확인
    if not verify_password(password_data.current_password, current_user.password_hash):
        logger.warning(f"잘못된 현재 비밀번호로 변경 시도: {current_user.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 올바르지 않습니다"
        )
    
    # 새 비밀번호와 현재 비밀번호가 같은지 확인
    if verify_password(password_data.new_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="새 비밀번호는 현재 비밀번호와 달라야 합니다"
        )
    
    # 비밀번호 업데이트
    current_user.password_hash = create_password_hash(password_data.new_password)
    db.commit()
    
    logger.info(f"비밀번호 변경 완료: {current_user.email}")
    
    return ChangePasswordResponse(
        message="비밀번호가 성공적으로 변경되었습니다"
    )


@router.get("/me", response_model=UserResponse, summary="현재 사용자 정보")
@log_api_call
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    현재 로그인한 사용자의 정보 조회
    """
    return UserResponse.from_orm(current_user)


@router.post("/validate-token", response_model=TokenValidationResponse, summary="토큰 검증")
@log_api_call
async def validate_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    토큰 유효성 검증
    
    - **token**: 검증할 토큰
    """
    user_id = verify_token(token)
    
    if not user_id:
        return TokenValidationResponse(
            valid=False,
            user=None,
            expires_at=None
        )
    
    # 사용자 정보 조회
    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        return TokenValidationResponse(
            valid=False,
            user=None,
            expires_at=None
        )
    
    return TokenValidationResponse(
        valid=True,
        user=UserResponse.from_orm(user),
        expires_at=None  # JWT에서 만료 시간 추출 로직 추가 필요
    )


# 비밀번호 재설정 기능 (이메일 발송 기능 구현 후 활성화)
@router.post("/password-reset", response_model=PasswordResetResponse, summary="비밀번호 재설정 요청")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    비밀번호 재설정 이메일 발송 요청
    
    - **email**: 재설정할 계정의 이메일 주소
    
    보안상 이메일 존재 여부와 관계없이 성공 응답을 반환합니다.
    """
    # 사용자 존재 확인 (보안상 결과를 노출하지 않음)
    user = db.query(User).filter(User.email == reset_data.email).first()
    
    if user and user.is_active:
        # TODO: 이메일 발송 기능 구현
        # - 재설정 토큰 생성
        # - 이메일 템플릿으로 발송
        logger.info(f"비밀번호 재설정 요청: {reset_data.email}")
        pass
    
    # 보안상 항상 성공 응답
    return PasswordResetResponse(
        message="비밀번호 재설정 이메일이 발송되었습니다. (구현 예정)"
    )