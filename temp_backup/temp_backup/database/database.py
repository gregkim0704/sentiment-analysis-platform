"""
데이터베이스 연결 및 설정
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator
import logging

from .models import Base

# 환경변수에서 데이터베이스 URL 가져오기
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://sentiment_user:sentiment_pass@localhost:5432/sentiment_db"
)

# SQLAlchemy 엔진 생성
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=300,    # 5분마다 연결 재생성
    echo=False,          # SQL 쿼리 로깅 (개발시에만 True)
)

# 세션 팩토리 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 로거 설정
logger = logging.getLogger(__name__)

def create_tables():
    """
    모든 테이블 생성
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("데이터베이스 테이블이 성공적으로 생성되었습니다.")
    except Exception as e:
        logger.error(f"테이블 생성 중 오류 발생: {e}")
        raise

def drop_tables():
    """
    모든 테이블 삭제 (개발용)
    """
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("모든 테이블이 삭제되었습니다.")
    except Exception as e:
        logger.error(f"테이블 삭제 중 오류 발생: {e}")
        raise

def get_db() -> Generator[Session, None, None]:
    """
    데이터베이스 세션 의존성 주입용 함수
    FastAPI에서 사용
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_database():
    """
    데이터베이스 초기화
    - 테이블 생성
    - 초기 데이터 삽입
    - 인덱스 최적화
    """
    try:
        # 테이블 생성
        create_tables()
        
        # 데이터베이스 연결 테스트
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            logger.info("데이터베이스 연결 테스트 성공")
        
        # 초기 데이터 삽입
        insert_initial_data()
        
        # 성능 최적화를 위한 추가 인덱스 생성
        create_performance_indexes()
        
        logger.info("데이터베이스 초기화가 완료되었습니다.")
        
    except Exception as e:
        logger.error(f"데이터베이스 초기화 중 오류 발생: {e}")
        raise

def insert_initial_data():
    """
    초기 데이터 삽입
    """
    from .models import User, Company, SystemConfig, UserRole
    from werkzeug.security import generate_password_hash
    
    db = SessionLocal()
    try:
        # 관리자 계정 생성 (이미 존재하지 않는 경우)
        admin_user = db.query(User).filter(User.email == "admin@sentiment-analysis.com").first()
        if not admin_user:
            admin_user = User(
                email="admin@sentiment-analysis.com",
                password_hash=generate_password_hash("admin123"),
                full_name="시스템 관리자",
                role=UserRole.ADMIN
            )
            db.add(admin_user)
            logger.info("관리자 계정이 생성되었습니다.")
        
        # 샘플 회사 데이터
        sample_companies = [
            {
                "name": "삼성전자",
                "stock_code": "005930",
                "industry": "전자/IT",
                "description": "글로벌 전자 및 IT 기업",
                "website_url": "https://www.samsung.com"
            },
            {
                "name": "SK하이닉스",
                "stock_code": "000660",
                "industry": "반도체",
                "description": "메모리 반도체 전문 기업",
                "website_url": "https://www.skhynix.com"
            },
            {
                "name": "NAVER",
                "stock_code": "035420",
                "industry": "인터넷/플랫폼",
                "description": "국내 최대 검색 포털 및 IT 서비스 기업",
                "website_url": "https://www.navercorp.com"
            }
        ]
        
        for company_data in sample_companies:
            existing_company = db.query(Company).filter(Company.name == company_data["name"]).first()
            if not existing_company:
                company = Company(**company_data)
                db.add(company)
                logger.info(f"샘플 회사 '{company_data['name']}'가 추가되었습니다.")
        
        # 시스템 설정 초기값
        system_configs = [
            {
                "key": "crawling_interval_hours",
                "value": "6",
                "description": "뉴스 크롤링 주기 (시간)"
            },
            {
                "key": "sentiment_analysis_model",
                "value": "klue/bert-base",
                "description": "사용할 센티멘트 분석 모델"
            },
            {
                "key": "max_articles_per_crawling",
                "value": "1000",
                "description": "한 번의 크롤링에서 수집할 최대 기사 수"
            },
            {
                "key": "alert_email_enabled",
                "value": "true",
                "description": "이메일 알림 활성화 여부"
            }
        ]
        
        for config_data in system_configs:
            existing_config = db.query(SystemConfig).filter(SystemConfig.key == config_data["key"]).first()
            if not existing_config:
                config = SystemConfig(**config_data)
                db.add(config)
        
        db.commit()
        logger.info("초기 데이터 삽입이 완료되었습니다.")
        
    except Exception as e:
        db.rollback()
        logger.error(f"초기 데이터 삽입 중 오류 발생: {e}")
        raise
    finally:
        db.close()

def create_performance_indexes():
    """
    성능 최적화를 위한 추가 인덱스 생성
    """
    try:
        with engine.connect() as connection:
            # 전문 검색을 위한 GIN 인덱스
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_news_articles_content_gin 
                ON news_articles USING gin(to_tsvector('korean', content));
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_news_articles_title_gin 
                ON news_articles USING gin(to_tsvector('korean', title));
            """))
            
            # 복합 인덱스 (자주 함께 검색되는 컬럼들)
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_news_articles_company_stakeholder_date 
                ON news_articles(company_id, stakeholder_type, published_date DESC);
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_sentiment_trends_company_stakeholder_date 
                ON sentiment_trends(company_id, stakeholder_type, date DESC);
            """))
            
            # 부분 인덱스 (활성 데이터만)
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_companies_active 
                ON companies(name) WHERE is_active = true;
            """))
            
            connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_active 
                ON users(email) WHERE is_active = true;
            """))
            
            connection.commit()
            logger.info("성능 최적화 인덱스가 생성되었습니다.")
            
    except Exception as e:
        logger.error(f"인덱스 생성 중 오류 발생: {e}")
        raise

def check_database_health() -> dict:
    """
    데이터베이스 상태 확인
    """
    try:
        with engine.connect() as connection:
            # 연결 테스트
            connection.execute(text("SELECT 1"))
            
            # 테이블 수 확인
            result = connection.execute(text("""
                SELECT COUNT(*) as table_count 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.fetchone()[0]
            
            # 활성 연결 수 확인
            result = connection.execute(text("""
                SELECT COUNT(*) as active_connections 
                FROM pg_stat_activity 
                WHERE state = 'active'
            """))
            active_connections = result.fetchone()[0]
            
            return {
                "status": "healthy",
                "table_count": table_count,
                "active_connections": active_connections,
                "database_url": DATABASE_URL.split("@")[1] if "@" in DATABASE_URL else "unknown"
            }
            
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    # 직접 실행시 데이터베이스 초기화
    logging.basicConfig(level=logging.INFO)
    init_database()