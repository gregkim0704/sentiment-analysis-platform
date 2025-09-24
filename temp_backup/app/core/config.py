"""
애플리케이션 설정 관리
"""

import os
from typing import List, Optional, Union
from pydantic import field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings
from enum import Enum


class Environment(str, Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 기본 애플리케이션 설정
    APP_NAME: str = "멀티 스테이크홀더 센티멘트 분석 플랫폼"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Environment = Environment.DEVELOPMENT
    DEBUG: bool = True
    
    # API 설정
    API_V1_STR: str = "/api/v1"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_WORKERS: int = 4
    API_RELOAD: bool = True
    
    # 데이터베이스 설정
    DATABASE_URL: str = "postgresql://sentiment_user:sentiment_pass@localhost:5432/sentiment_db"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = "sentiment_db"
    DB_USER: str = "sentiment_user"
    DB_PASSWORD: str = "sentiment_pass"
    
    # Redis 설정
    REDIS_URL: str = "redis://localhost:6379"
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # JWT 토큰 설정
    JWT_SECRET_KEY: str = "your-very-secure-secret-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # CORS 설정
    CORS_ORIGINS: List[AnyHttpUrl] = [
        "http://localhost:3000",
        "http://localhost:8080"
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # 허용된 호스트
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # 이메일 설정
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    SENDER_EMAIL: str = "noreply@sentiment-analysis.com"
    SENDER_NAME: str = "센티멘트 분석 플랫폼"
    
    # 외부 API 키
    OPENAI_API_KEY: Optional[str] = None
    NAVER_CLIENT_ID: Optional[str] = None
    NAVER_CLIENT_SECRET: Optional[str] = None
    GOOGLE_API_KEY: Optional[str] = None
    GOOGLE_CSE_ID: Optional[str] = None
    
    # 소셜 미디어 API
    TWITTER_BEARER_TOKEN: Optional[str] = None
    FACEBOOK_ACCESS_TOKEN: Optional[str] = None
    
    # 알림 설정
    SLACK_WEBHOOK_URL: Optional[str] = None
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    
    # 로깅 설정
    LOG_LEVEL: LogLevel = LogLevel.INFO
    LOG_FORMAT: str = "json"
    LOG_FILE_PATH: str = "./logs/app.log"
    LOG_MAX_SIZE: str = "10MB"
    LOG_BACKUP_COUNT: int = 5
    
    # 모니터링 설정
    ENABLE_MONITORING: bool = True
    PROMETHEUS_PORT: int = 9090
    GRAFANA_PORT: int = 3000
    SENTRY_DSN: Optional[str] = None
    
    # 크롤링 설정
    CRAWLING_INTERVAL_HOURS: int = 6
    MAX_ARTICLES_PER_CRAWLING: int = 1000
    CRAWLING_DELAY_SECONDS: int = 1
    USER_AGENT: str = "SentimentAnalysisPlatform/1.0"
    CRAWLING_TIMEOUT_SECONDS: int = 30
    
    # 센티멘트 분석 모델 설정
    SENTIMENT_MODEL_NAME: str = "klue/bert-base"
    SENTIMENT_MODEL_PATH: str = "./models/sentiment"
    SENTIMENT_CONFIDENCE_THRESHOLD: float = 0.7
    BATCH_SIZE: int = 32
    MAX_SEQUENCE_LENGTH: int = 512
    
    # 캐시 설정
    CACHE_TTL_SECONDS: int = 3600
    CACHE_MAX_SIZE: int = 1000
    
    # 파일 업로드 설정
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_FILE_EXTENSIONS: List[str] = ["txt", "csv", "xlsx", "json"]
    UPLOAD_PATH: str = "./uploads"
    
    # 보안 설정
    SECRET_KEY: str = "your-secret-key-for-sessions"
    BCRYPT_ROUNDS: int = 12
    SESSION_TIMEOUT_MINUTES: int = 60
    MAX_LOGIN_ATTEMPTS: int = 5
    LOCKOUT_DURATION_MINUTES: int = 15
    
    # 데이터 보관 정책
    DATA_RETENTION_DAYS: int = 365
    CLEANUP_INTERVAL_HOURS: int = 24
    ARCHIVE_OLD_DATA: bool = True
    
    # 성능 설정
    MAX_CONCURRENT_REQUESTS: int = 100
    REQUEST_TIMEOUT_SECONDS: int = 30
    CONNECTION_POOL_SIZE: int = 20
    MAX_OVERFLOW: int = 30
    
    # 개발 도구 설정
    ENABLE_SWAGGER: bool = True
    ENABLE_REDOC: bool = True
    ENABLE_DEBUG_TOOLBAR: bool = False
    
    # 테스트 설정
    TEST_DATABASE_URL: str = "postgresql://test_user:test_pass@localhost:5432/test_sentiment_db"
    TEST_REDIS_URL: str = "redis://localhost:6379/1"
    
    # 백업 설정
    BACKUP_ENABLED: bool = True
    BACKUP_SCHEDULE: str = "0 2 * * *"  # 매일 새벽 2시
    BACKUP_RETENTION_DAYS: int = 30
    BACKUP_PATH: str = "./backups"
    
    # 알림 임계값 설정
    ALERT_SENTIMENT_THRESHOLD: float = -1.5
    ALERT_ARTICLE_COUNT_THRESHOLD: int = 50
    ALERT_ERROR_RATE_THRESHOLD: float = 0.05
    
    # 외부 서비스 설정
    WEBHOOK_TIMEOUT_SECONDS: int = 10
    WEBHOOK_RETRY_COUNT: int = 3
    WEBHOOK_RETRY_DELAY_SECONDS: int = 5
    
    # 국제화 설정
    DEFAULT_LANGUAGE: str = "ko"
    SUPPORTED_LANGUAGES: List[str] = ["ko", "en"]
    TIMEZONE: str = "Asia/Seoul"
    
    # 기능 플래그
    ENABLE_REAL_TIME_ANALYSIS: bool = True
    ENABLE_ADVANCED_ANALYTICS: bool = True
    ENABLE_EXPORT_FEATURES: bool = True
    ENABLE_API_RATE_LIMITING: bool = True
    
    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    @field_validator("JWT_SECRET_KEY")
    @classmethod
    def validate_jwt_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters long")
        return v
    
    @field_validator("ENVIRONMENT")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        if v not in [env.value for env in Environment]:
            raise ValueError(f"ENVIRONMENT must be one of {[env.value for env in Environment]}")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 설정 인스턴스 생성
settings = Settings()

# 환경별 설정 오버라이드
if settings.ENVIRONMENT == Environment.PRODUCTION:
    settings.DEBUG = False
    settings.API_RELOAD = False
    settings.ENABLE_SWAGGER = False
    settings.ENABLE_REDOC = False
    settings.LOG_LEVEL = LogLevel.WARNING

elif settings.ENVIRONMENT == Environment.TESTING:
    settings.DATABASE_URL = settings.TEST_DATABASE_URL
    settings.REDIS_URL = settings.TEST_REDIS_URL
    settings.LOG_LEVEL = LogLevel.DEBUG