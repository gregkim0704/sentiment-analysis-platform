"""
예외 처리 및 에러 핸들러
"""

from fastapi import FastAPI, Request, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError
from pydantic import ValidationError
import traceback
import time

from app.core.logging import logger
from app.core.config import settings


class SentimentAnalysisException(Exception):
    """기본 애플리케이션 예외"""
    
    def __init__(self, message: str, status_code: int = 500, details: dict = None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(self.message)


class DatabaseException(SentimentAnalysisException):
    """데이터베이스 관련 예외"""
    
    def __init__(self, message: str = "데이터베이스 오류가 발생했습니다", details: dict = None):
        super().__init__(message, status.HTTP_500_INTERNAL_SERVER_ERROR, details)


class AuthenticationException(SentimentAnalysisException):
    """인증 관련 예외"""
    
    def __init__(self, message: str = "인증에 실패했습니다", details: dict = None):
        super().__init__(message, status.HTTP_401_UNAUTHORIZED, details)


class AuthorizationException(SentimentAnalysisException):
    """권한 관련 예외"""
    
    def __init__(self, message: str = "권한이 없습니다", details: dict = None):
        super().__init__(message, status.HTTP_403_FORBIDDEN, details)


class ValidationException(SentimentAnalysisException):
    """데이터 검증 예외"""
    
    def __init__(self, message: str = "입력 데이터가 올바르지 않습니다", details: dict = None):
        super().__init__(message, status.HTTP_422_UNPROCESSABLE_ENTITY, details)


class NotFoundError(SentimentAnalysisException):
    """리소스를 찾을 수 없음"""
    
    def __init__(self, message: str = "요청한 리소스를 찾을 수 없습니다", details: dict = None):
        super().__init__(message, status.HTTP_404_NOT_FOUND, details)


class RateLimitException(SentimentAnalysisException):
    """속도 제한 예외"""
    
    def __init__(self, message: str = "요청 한도를 초과했습니다", details: dict = None):
        super().__init__(message, status.HTTP_429_TOO_MANY_REQUESTS, details)


class ExternalServiceException(SentimentAnalysisException):
    """외부 서비스 오류"""
    
    def __init__(self, message: str = "외부 서비스 오류가 발생했습니다", details: dict = None):
        super().__init__(message, status.HTTP_502_BAD_GATEWAY, details)


def create_error_response(
    status_code: int,
    message: str,
    details: dict = None,
    request_id: str = None
) -> dict:
    """표준 에러 응답 생성"""
    error_response = {
        "error": {
            "code": status_code,
            "message": message,
            "timestamp": str(int(time.time())),
        }
    }
    
    if details:
        error_response["error"]["details"] = details
    
    if request_id:
        error_response["error"]["request_id"] = request_id
    
    if settings.DEBUG and details and "traceback" in details:
        error_response["error"]["traceback"] = details["traceback"]
    
    return error_response


async def sentiment_analysis_exception_handler(
    request: Request, 
    exc: SentimentAnalysisException
) -> JSONResponse:
    """애플리케이션 예외 핸들러"""
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"애플리케이션 예외 발생: {exc.message}",
        extra={
            "status_code": exc.status_code,
            "details": exc.details,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            exc.status_code,
            exc.message,
            exc.details,
            request_id
        )
    )


async def http_exception_handler(
    request: Request, 
    exc: HTTPException
) -> JSONResponse:
    """HTTP 예외 핸들러"""
    request_id = getattr(request.state, "request_id", None)
    
    logger.warning(
        f"HTTP 예외 발생: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=exc.status_code,
        content=create_error_response(
            exc.status_code,
            exc.detail,
            request_id=request_id
        )
    )


async def validation_exception_handler(
    request: Request, 
    exc: RequestValidationError
) -> JSONResponse:
    """요청 검증 예외 핸들러"""
    request_id = getattr(request.state, "request_id", None)
    
    # 검증 오류 상세 정보 추출
    errors = []
    for error in exc.errors():
        errors.append({
            "field": " -> ".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })
    
    logger.warning(
        f"요청 검증 실패: {len(errors)}개 오류",
        extra={
            "errors": errors,
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method
        }
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=create_error_response(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "입력 데이터 검증에 실패했습니다",
            {"validation_errors": errors},
            request_id
        )
    )


async def sqlalchemy_exception_handler(
    request: Request, 
    exc: SQLAlchemyError
) -> JSONResponse:
    """SQLAlchemy 예외 핸들러"""
    import time
    
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"데이터베이스 오류 발생: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc() if settings.DEBUG else None
        }
    )
    
    # 프로덕션 환경에서는 상세 오류 정보 숨김
    if settings.ENVIRONMENT == "production":
        message = "데이터베이스 오류가 발생했습니다"
        details = None
    else:
        message = f"데이터베이스 오류: {str(exc)}"
        details = {"traceback": traceback.format_exc()}
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            details,
            request_id
        )
    )


async def general_exception_handler(
    request: Request, 
    exc: Exception
) -> JSONResponse:
    """일반 예외 핸들러"""
    import time
    
    request_id = getattr(request.state, "request_id", None)
    
    logger.error(
        f"예상치 못한 오류 발생: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "traceback": traceback.format_exc()
        }
    )
    
    # 프로덕션 환경에서는 상세 오류 정보 숨김
    if settings.ENVIRONMENT == "production":
        message = "서버 내부 오류가 발생했습니다"
        details = None
    else:
        message = f"서버 오류: {str(exc)}"
        details = {"traceback": traceback.format_exc()}
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=create_error_response(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            message,
            details,
            request_id
        )
    )


def setup_exception_handlers(app: FastAPI):
    """예외 핸들러 등록"""
    
    # 커스텀 예외 핸들러
    app.add_exception_handler(
        SentimentAnalysisException, 
        sentiment_analysis_exception_handler
    )
    
    # HTTP 예외 핸들러
    app.add_exception_handler(
        StarletteHTTPException, 
        http_exception_handler
    )
    
    # 요청 검증 예외 핸들러
    app.add_exception_handler(
        RequestValidationError, 
        validation_exception_handler
    )
    
    # SQLAlchemy 예외 핸들러
    app.add_exception_handler(
        SQLAlchemyError, 
        sqlalchemy_exception_handler
    )
    
    # 일반 예외 핸들러
    app.add_exception_handler(
        Exception, 
        general_exception_handler
    )