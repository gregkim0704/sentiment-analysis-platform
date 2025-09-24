"""
멀티 스테이크홀더 센티멘트 분석 플랫폼 - 데이터베이스 모델
"""

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float, Boolean, 
    ForeignKey, Enum, Index, UniqueConstraint, JSON
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()

# Enum 정의
class UserRole(enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

class StakeholderType(enum.Enum):
    CUSTOMER = "customer"          # 고객
    INVESTOR = "investor"          # 투자자
    EMPLOYEE = "employee"          # 직원
    GOVERNMENT = "government"      # 정부/규제기관
    MEDIA = "media"               # 언론
    PARTNER = "partner"           # 파트너/협력사
    COMPETITOR = "competitor"     # 경쟁사
    COMMUNITY = "community"       # 지역사회

class SentimentScore(enum.Enum):
    VERY_NEGATIVE = "very_negative"  # -2
    NEGATIVE = "negative"            # -1
    NEUTRAL = "neutral"              # 0
    POSITIVE = "positive"            # 1
    VERY_POSITIVE = "very_positive"  # 2

class NewsSource(enum.Enum):
    NAVER = "naver"
    DAUM = "daum"
    GOOGLE = "google"
    COMPANY_WEBSITE = "company_website"
    SOCIAL_MEDIA = "social_media"
    PRESS_RELEASE = "press_release"

# 사용자 관리
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.VIEWER, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login = Column(DateTime(timezone=True))
    
    # 관계
    analysis_requests = relationship("AnalysisRequest", back_populates="user")

# 회사 정보
class Company(Base):
    __tablename__ = "companies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), unique=True, index=True, nullable=False)
    stock_code = Column(String(20), unique=True, index=True)  # 주식 코드
    industry = Column(String(100), nullable=False)
    description = Column(Text)
    website_url = Column(String(500))
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계
    news_articles = relationship("NewsArticle", back_populates="company")
    sentiment_trends = relationship("SentimentTrend", back_populates="company")
    analysis_requests = relationship("AnalysisRequest", back_populates="company")

# 뉴스 기사
class NewsArticle(Base):
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    url = Column(String(1000), unique=True, nullable=False)
    source = Column(Enum(NewsSource), nullable=False)
    author = Column(String(100))
    published_date = Column(DateTime(timezone=True), nullable=False)
    collected_date = Column(DateTime(timezone=True), server_default=func.now())
    
    # 센티멘트 분석 결과
    sentiment_score = Column(Enum(SentimentScore))
    sentiment_confidence = Column(Float)  # 0.0 ~ 1.0
    stakeholder_type = Column(Enum(StakeholderType))
    
    # 키워드 및 메타데이터
    keywords = Column(JSON)  # 추출된 키워드 리스트
    summary = Column(Text)   # 기사 요약
    
    # 관계
    company = relationship("Company", back_populates="news_articles")
    
    # 인덱스
    __table_args__ = (
        Index('idx_news_company_date', 'company_id', 'published_date'),
        Index('idx_news_stakeholder_sentiment', 'stakeholder_type', 'sentiment_score'),
        Index('idx_news_source_date', 'source', 'published_date'),
    )

# 센티멘트 트렌드 (일별 집계)
class SentimentTrend(Base):
    __tablename__ = "sentiment_trends"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    stakeholder_type = Column(Enum(StakeholderType), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False)
    
    # 센티멘트 통계
    total_articles = Column(Integer, default=0)
    positive_count = Column(Integer, default=0)
    negative_count = Column(Integer, default=0)
    neutral_count = Column(Integer, default=0)
    
    # 평균 센티멘트 점수 (-2 ~ +2)
    avg_sentiment_score = Column(Float, default=0.0)
    sentiment_volatility = Column(Float, default=0.0)  # 센티멘트 변동성
    
    # 주요 키워드 (상위 10개)
    top_keywords = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 관계
    company = relationship("Company", back_populates="sentiment_trends")
    
    # 유니크 제약조건
    __table_args__ = (
        UniqueConstraint('company_id', 'stakeholder_type', 'date', name='uq_sentiment_trend'),
        Index('idx_sentiment_company_stakeholder_date', 'company_id', 'stakeholder_type', 'date'),
    )

# 분석 요청 (사용자가 요청한 분석)
class AnalysisRequest(Base):
    __tablename__ = "analysis_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    # 분석 설정
    stakeholder_types = Column(JSON)  # 분석할 스테이크홀더 타입 리스트
    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=False)
    keywords = Column(JSON)  # 특정 키워드 필터
    
    # 분석 결과
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    result_summary = Column(JSON)  # 분석 결과 요약
    insights = Column(Text)  # AI가 생성한 인사이트
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True))
    
    # 관계
    user = relationship("User", back_populates="analysis_requests")
    company = relationship("Company", back_populates="analysis_requests")

# 알림 설정
class AlertRule(Base):
    __tablename__ = "alert_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    
    name = Column(String(200), nullable=False)
    description = Column(Text)
    
    # 알림 조건
    stakeholder_type = Column(Enum(StakeholderType))
    sentiment_threshold = Column(Float)  # 센티멘트 임계값
    article_count_threshold = Column(Integer)  # 기사 수 임계값
    
    # 알림 설정
    is_active = Column(Boolean, default=True)
    notification_channels = Column(JSON)  # email, slack, webhook 등
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 알림 로그
class AlertLog(Base):
    __tablename__ = "alert_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_rule_id = Column(Integer, ForeignKey("alert_rules.id"), nullable=False)
    
    triggered_at = Column(DateTime(timezone=True), server_default=func.now())
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info")  # info, warning, critical
    
    # 알림 발송 상태
    sent_channels = Column(JSON)  # 성공적으로 발송된 채널들
    failed_channels = Column(JSON)  # 발송 실패한 채널들

# 시스템 설정
class SystemConfig(Base):
    __tablename__ = "system_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 크롤링 작업 로그
class CrawlingJob(Base):
    __tablename__ = "crawling_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False)
    source = Column(Enum(NewsSource), nullable=False)
    
    # 작업 정보
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    start_time = Column(DateTime(timezone=True), server_default=func.now())
    end_time = Column(DateTime(timezone=True))
    
    # 결과 통계
    articles_found = Column(Integer, default=0)
    articles_processed = Column(Integer, default=0)
    articles_saved = Column(Integer, default=0)
    
    error_message = Column(Text)
    
    # 인덱스
    __table_args__ = (
        Index('idx_crawling_company_source_time', 'company_id', 'source', 'start_time'),
    )