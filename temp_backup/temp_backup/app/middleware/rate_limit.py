"""
속도 제한 미들웨어
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.redis import get_redis
from app.core.security import RateLimiter
from app.core.config import settings
from app.core.logging import logger


class RateLimitMiddleware(BaseHTTPMiddleware):
    """API 속도 제한 미들웨어"""
    
    def __init__(self, app, calls_per_minute: int = None):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute or 1000  # 기본값
        self.rate_limiter = RateLimiter(get_redis())
        
        # 경로별 제한 설정
        self.path_limits = {
            "/api/v1/auth/login": 10,  # 로그인은 더 엄격하게
            "/api/v1/auth/register": 5,  # 회원가입도 엄격하게
            "/api/v1/crawling/start": 2,  # 크롤링 시작은 매우 제한적
            "/api/v1/analysis/request": 20,  # 분석 요청 제한
        }
    
    async def dispatch(self, request: Request, call_next):
        # 속도 제한 비활성화된 경우 통과
        if not settings.ENABLE_API_RATE_LIMITING:
            return await call_next(request)
        
        # 헬스체크 및 메트릭 엔드포인트는 제외
        if request.url.path in ["/health", "/metrics", "/"]:
            return await call_next(request)
        
        # 클라이언트 식별 (IP 주소 기반)
        client_ip = request.client.host
        
        # 경로별 제한 확인
        path_limit = self.path_limits.get(request.url.path, self.calls_per_minute)
        
        # 속도 제한 키 생성
        rate_limit_key = f"rate_limit:{client_ip}:{request.url.path}"
        
        # 속도 제한 확인
        is_allowed, limit_info = self.rate_limiter.is_allowed(
            rate_limit_key, 
            path_limit, 
            60  # 1분 윈도우
        )
        
        if not is_allowed:
            logger.warning(
                f"속도 제한 초과: {client_ip} - {request.url.path}",
                extra={
                    "client_ip": client_ip,
                    "path": request.url.path,
                    "limit": path_limit,
                    "window": 60
                }
            )
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": {
                        "code": 429,
                        "message": "요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.",
                        "details": {
                            "limit": limit_info["limit"],
                            "remaining": limit_info["remaining"],
                            "reset_time": limit_info["reset_time"]
                        }
                    }
                },
                headers={
                    "X-RateLimit-Limit": str(limit_info["limit"]),
                    "X-RateLimit-Remaining": str(limit_info["remaining"]),
                    "X-RateLimit-Reset": str(limit_info["reset_time"]),
                    "Retry-After": str(limit_info["reset_time"])
                }
            )
        
        # 요청 처리
        response = await call_next(request)
        
        # 속도 제한 정보를 응답 헤더에 추가
        response.headers["X-RateLimit-Limit"] = str(limit_info["limit"])
        response.headers["X-RateLimit-Remaining"] = str(limit_info["remaining"])
        response.headers["X-RateLimit-Reset"] = str(limit_info["reset_time"])
        
        return response