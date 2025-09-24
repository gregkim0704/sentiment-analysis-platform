"""
로깅 설정 및 관리
"""

import logging
import sys
from pathlib import Path
from loguru import logger as loguru_logger
from app.core.config import settings


class InterceptHandler(logging.Handler):
    """표준 로깅을 Loguru로 리다이렉트"""
    
    def emit(self, record):
        # 해당하는 Loguru 레벨 찾기
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # 호출자 정보 찾기
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """로깅 설정"""
    
    # 기존 핸들러 제거
    loguru_logger.remove()
    
    # 로그 디렉토리 생성
    log_path = Path(settings.LOG_FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 로그 포맷 설정
    if settings.LOG_FORMAT == "json":
        log_format = (
            "{"
            '"time": "{time:YYYY-MM-DD HH:mm:ss.SSS}", '
            '"level": "{level}", '
            '"module": "{module}", '
            '"function": "{function}", '
            '"line": {line}, '
            '"message": "{message}"'
            "}"
        )
    else:
        log_format = (
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        )
    
    # 콘솔 핸들러 추가
    loguru_logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True if settings.LOG_FORMAT != "json" else False,
        serialize=True if settings.LOG_FORMAT == "json" else False
    )
    
    # 파일 핸들러 추가
    loguru_logger.add(
        settings.LOG_FILE_PATH,
        format=log_format,
        level=settings.LOG_LEVEL,
        rotation=settings.LOG_MAX_SIZE,
        retention=f"{settings.LOG_BACKUP_COUNT} files",
        compression="zip",
        serialize=True if settings.LOG_FORMAT == "json" else False,
        encoding="utf-8"
    )
    
    # 에러 로그 별도 파일
    error_log_path = log_path.parent / "error.log"
    loguru_logger.add(
        str(error_log_path),
        format=log_format,
        level="ERROR",
        rotation=settings.LOG_MAX_SIZE,
        retention=f"{settings.LOG_BACKUP_COUNT} files",
        compression="zip",
        serialize=True if settings.LOG_FORMAT == "json" else False,
        encoding="utf-8"
    )
    
    # 표준 로깅을 Loguru로 리다이렉트
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # 특정 로거들의 레벨 조정
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "fastapi"]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.setLevel(logging.INFO)
    
    # SQLAlchemy 로깅 (개발 환경에서만)
    if settings.ENVIRONMENT == "development":
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


# 로거 인스턴스 (전역 사용)
logger = loguru_logger


def get_logger(name: str = None):
    """로거 인스턴스 반환"""
    if name:
        return logger.bind(name=name)
    return logger


# 로깅 데코레이터
def log_execution_time(func):
    """함수 실행 시간 로깅 데코레이터"""
    import time
    from functools import wraps
    
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} 실행 완료 - {execution_time:.3f}초")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 실행 실패 - {execution_time:.3f}초, 오류: {e}")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} 실행 완료 - {execution_time:.3f}초")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 실행 실패 - {execution_time:.3f}초, 오류: {e}")
            raise
    
    import asyncio
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


def log_api_call(func):
    """API 호출 로깅 데코레이터"""
    from functools import wraps
    
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # 요청 정보 로깅
        logger.info(f"API 호출: {func.__name__}")
        
        try:
            result = await func(*args, **kwargs)
            logger.info(f"API 응답 성공: {func.__name__}")
            return result
        except Exception as e:
            logger.error(f"API 응답 실패: {func.__name__}, 오류: {e}")
            raise
    
    return wrapper