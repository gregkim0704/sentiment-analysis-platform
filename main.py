"""
멀티 스테이크홀더 센티멘트 분석 플랫폼 - 메인 애플리케이션
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import time
import os
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import setup_logging, logger
from app.api.v1.api import api_router
from app.core.database import init_database
from app.core.exceptions import setup_exception_handlers
from app.middleware.security import SecurityMiddleware
# from app.middleware.rate_limit import RateLimitMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    # 시작 시 실행
    logger.info("🚀 애플리케이션 시작 중...")
    
    # 로깅 설정
    setup_logging()
    
    # 데이터베이스 초기화 (임시 비활성화)
    try:
        # init_database()
        logger.info("✅ 데이터베이스 초기화 건너뜀 (개발 모드)")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        # raise
    
    # 필요한 디렉토리 생성
    os.makedirs("logs", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    os.makedirs("static", exist_ok=True)
    os.makedirs("uploads", exist_ok=True)
    
    logger.info("✅ 애플리케이션 시작 완료")
    
    yield
    
    # 종료 시 실행
    logger.info("🛑 애플리케이션 종료 중...")


# FastAPI 애플리케이션 생성
app = FastAPI(
    title=settings.APP_NAME,
    description="다양한 스테이크홀더의 센티멘트를 실시간으로 분석하는 플랫폼",
    version=settings.APP_VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.ENVIRONMENT != "production" else None,
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    lifespan=lifespan
)

# CORS 미들웨어 설정
if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.CORS_ORIGINS],
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# 보안 미들웨어
app.add_middleware(SecurityMiddleware)

# 속도 제한 미들웨어 (임시 비활성화)
# app.add_middleware(RateLimitMiddleware)

# 신뢰할 수 있는 호스트 미들웨어
app.add_middleware(
    TrustedHostMiddleware, 
    allowed_hosts=settings.ALLOWED_HOSTS
)

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")

# 예외 처리기 설정
setup_exception_handlers(app)

# API 라우터 등록
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """요청 처리 시간 측정 미들웨어"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "message": "멀티 스테이크홀더 센티멘트 분석 플랫폼",
        "version": settings.APP_VERSION,
        "status": "running",
        "docs_url": "/docs" if settings.ENVIRONMENT != "production" else None
    }


@app.get("/health")
async def health_check():
    """헬스 체크 엔드포인트"""
    try:
        # 임시로 기본 헬스 체크만 수행
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "database": {"status": "disabled"},
            "redis": {"status": "disabled"}
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        raise HTTPException(status_code=503, detail="Service Unavailable")


@app.get("/metrics")
async def metrics():
    """Prometheus 메트릭 엔드포인트"""
    from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
    from fastapi.responses import Response
    
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD,
        log_level=settings.LOG_LEVEL.lower()
    )