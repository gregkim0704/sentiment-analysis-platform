"""
보안 미들웨어
"""

import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.logging import logger


class SecurityMiddleware(BaseHTTPMiddleware):
    """보안 헤더 및 요청 추적 미들웨어"""
    
    async def dispatch(self, request: Request, call_next):
        # 요청 ID 생성
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # 요청 로깅
        logger.info(
            f"요청 시작: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "query_params": str(request.query_params),
                "client_ip": request.client.host,
                "user_agent": request.headers.get("user-agent", "")
            }
        )
        
        # 요청 처리
        response = await call_next(request)
        
        # 보안 헤더 추가
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # 응답 로깅
        logger.info(
            f"요청 완료: {request.method} {request.url.path} - {response.status_code}",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "response_size": response.headers.get("content-length", "unknown")
            }
        )
        
        return response