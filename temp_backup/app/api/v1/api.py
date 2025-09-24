"""
API v1 라우터 통합
"""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    auth,
    users,
    companies,
    news,
    sentiment,
    analysis,
    alerts,
    dashboard,
    admin,
    crawling,
    stakeholders,
    test
)

api_router = APIRouter()

# 인증 관련 엔드포인트
api_router.include_router(
    auth.router, 
    prefix="/auth", 
    tags=["인증"]
)

# 사용자 관리 엔드포인트
api_router.include_router(
    users.router, 
    prefix="/users", 
    tags=["사용자"]
)

# 회사 관리 엔드포인트
api_router.include_router(
    companies.router, 
    prefix="/companies", 
    tags=["회사"]
)

# 뉴스 관리 엔드포인트
api_router.include_router(
    news.router, 
    prefix="/news", 
    tags=["뉴스"]
)

# 센티멘트 분석 엔드포인트
api_router.include_router(
    sentiment.router, 
    prefix="/sentiment", 
    tags=["센티멘트 분석"]
)

# 분석 요청 엔드포인트
api_router.include_router(
    analysis.router, 
    prefix="/analysis", 
    tags=["분석 요청"]
)

# 알림 관리 엔드포인트
api_router.include_router(
    alerts.router, 
    prefix="/alerts", 
    tags=["알림"]
)

# 대시보드 엔드포인트
api_router.include_router(
    dashboard.router, 
    prefix="/dashboard", 
    tags=["대시보드"]
)

# 관리자 엔드포인트
api_router.include_router(
    admin.router, 
    prefix="/admin", 
    tags=["관리자"]
)

# 크롤링 엔드포인트
api_router.include_router(
    crawling.router, 
    prefix="/crawling", 
    tags=["크롤링"]
)

# 스테이크홀더 엔드포인트
api_router.include_router(
    stakeholders.router, 
    prefix="/stakeholders", 
    tags=["스테이크홀더"]
)

# 테스트 엔드포인트 (개발용)
api_router.include_router(
    test.router, 
    prefix="/test", 
    tags=["테스트"]
)