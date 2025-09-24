#!/usr/bin/env python3
"""
데이터베이스 연결 및 기능 테스트 스크립트
"""

import sys
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.database import SessionLocal, check_database_health
from database.models import (
    User, Company, NewsArticle, SentimentTrend, 
    StakeholderType, SentimentScore, NewsSource
)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_database_connection():
    """데이터베이스 연결 테스트"""
    logger.info("🔍 데이터베이스 연결 테스트 중...")
    
    try:
        health_status = check_database_health()
        if health_status["status"] == "healthy":
            logger.info("✅ 데이터베이스 연결 성공")
            logger.info(f"   - 테이블 수: {health_status['table_count']}")
            logger.info(f"   - 활성 연결: {health_status['active_connections']}")
            return True
        else:
            logger.error("❌ 데이터베이스 연결 실패")
            logger.error(f"   - 오류: {health_status.get('error')}")
            return False
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 테스트 실패: {e}")
        return False

def test_basic_crud():
    """기본 CRUD 작업 테스트"""
    logger.info("🔍 기본 CRUD 작업 테스트 중...")
    
    db = SessionLocal()
    try:
        # 1. 사용자 조회 테스트
        users = db.query(User).all()
        logger.info(f"   - 등록된 사용자 수: {len(users)}")
        
        # 2. 회사 조회 테스트
        companies = db.query(Company).all()
        logger.info(f"   - 등록된 회사 수: {len(companies)}")
        
        # 3. 뉴스 기사 조회 테스트
        articles = db.query(NewsArticle).all()
        logger.info(f"   - 등록된 뉴스 기사 수: {len(articles)}")
        
        # 4. 센티멘트 트렌드 조회 테스트
        trends = db.query(SentimentTrend).all()
        logger.info(f"   - 센티멘트 트렌드 데이터 수: {len(trends)}")
        
        logger.info("✅ 기본 CRUD 작업 테스트 성공")
        return True
        
    except Exception as e:
        logger.error(f"❌ 기본 CRUD 작업 테스트 실패: {e}")
        return False
    finally:
        db.close()

def test_sample_data_insertion():
    """샘플 데이터 삽입 테스트"""
    logger.info("🔍 샘플 데이터 삽입 테스트 중...")
    
    db = SessionLocal()
    try:
        # 테스트용 회사가 있는지 확인
        test_company = db.query(Company).filter(Company.name == "삼성전자").first()
        if not test_company:
            logger.error("❌ 테스트용 회사 데이터가 없습니다.")
            return False
        
        # 샘플 뉴스 기사 생성
        sample_article = NewsArticle(
            company_id=test_company.id,
            title="삼성전자, 새로운 반도체 기술 발표",
            content="삼성전자가 차세대 반도체 기술을 발표했습니다. 이 기술은 기존 대비 성능이 30% 향상되었습니다.",
            url=f"https://test-news.com/article/{datetime.now().timestamp()}",
            source=NewsSource.COMPANY_WEBSITE,
            author="테스트 기자",
            published_date=datetime.now(),
            sentiment_score=SentimentScore.POSITIVE,
            sentiment_confidence=0.85,
            stakeholder_type=StakeholderType.INVESTOR,
            keywords=["반도체", "기술", "성능", "향상"],
            summary="삼성전자의 새로운 반도체 기술 발표 소식"
        )
        
        db.add(sample_article)
        db.commit()
        
        logger.info("✅ 샘플 데이터 삽입 테스트 성공")
        logger.info(f"   - 생성된 기사 ID: {sample_article.id}")
        return True
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ 샘플 데이터 삽입 테스트 실패: {e}")
        return False
    finally:
        db.close()

def test_complex_queries():
    """복잡한 쿼리 테스트"""
    logger.info("🔍 복잡한 쿼리 테스트 중...")
    
    db = SessionLocal()
    try:
        # 1. 회사별 센티멘트 평균 계산
        from sqlalchemy import func
        
        sentiment_avg = db.query(
            Company.name,
            func.avg(
                func.case(
                    (NewsArticle.sentiment_score == SentimentScore.VERY_NEGATIVE, -2),
                    (NewsArticle.sentiment_score == SentimentScore.NEGATIVE, -1),
                    (NewsArticle.sentiment_score == SentimentScore.NEUTRAL, 0),
                    (NewsArticle.sentiment_score == SentimentScore.POSITIVE, 1),
                    (NewsArticle.sentiment_score == SentimentScore.VERY_POSITIVE, 2),
                    else_=0
                )
            ).label('avg_sentiment')
        ).join(NewsArticle).group_by(Company.name).all()
        
        logger.info(f"   - 회사별 센티멘트 평균 계산 결과: {len(sentiment_avg)}개")
        
        # 2. 최근 7일간 기사 수 조회
        recent_articles = db.query(NewsArticle).filter(
            NewsArticle.published_date >= datetime.now() - timedelta(days=7)
        ).count()
        
        logger.info(f"   - 최근 7일간 기사 수: {recent_articles}개")
        
        # 3. 스테이크홀더별 기사 분포
        stakeholder_dist = db.query(
            NewsArticle.stakeholder_type,
            func.count(NewsArticle.id)
        ).group_by(NewsArticle.stakeholder_type).all()
        
        logger.info(f"   - 스테이크홀더별 기사 분포: {len(stakeholder_dist)}개 그룹")
        
        logger.info("✅ 복잡한 쿼리 테스트 성공")
        return True
        
    except Exception as e:
        logger.error(f"❌ 복잡한 쿼리 테스트 실패: {e}")
        return False
    finally:
        db.close()

def test_database_performance():
    """데이터베이스 성능 테스트"""
    logger.info("🔍 데이터베이스 성능 테스트 중...")
    
    db = SessionLocal()
    try:
        import time
        
        # 인덱스 효율성 테스트
        start_time = time.time()
        
        # 회사명으로 검색 (인덱스 사용)
        company = db.query(Company).filter(Company.name == "삼성전자").first()
        
        search_time = time.time() - start_time
        logger.info(f"   - 회사명 검색 시간: {search_time:.4f}초")
        
        if company:
            # 해당 회사의 최근 기사 검색 (복합 인덱스 사용)
            start_time = time.time()
            
            recent_articles = db.query(NewsArticle).filter(
                NewsArticle.company_id == company.id,
                NewsArticle.published_date >= datetime.now() - timedelta(days=30)
            ).limit(100).all()
            
            query_time = time.time() - start_time
            logger.info(f"   - 최근 기사 검색 시간: {query_time:.4f}초")
            logger.info(f"   - 검색된 기사 수: {len(recent_articles)}개")
        
        logger.info("✅ 데이터베이스 성능 테스트 완료")
        return True
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 성능 테스트 실패: {e}")
        return False
    finally:
        db.close()

def main():
    """메인 테스트 함수"""
    logger.info("=" * 60)
    logger.info("멀티 스테이크홀더 센티멘트 분석 플랫폼 DB 테스트 시작")
    logger.info("=" * 60)
    
    tests = [
        ("데이터베이스 연결", test_database_connection),
        ("기본 CRUD 작업", test_basic_crud),
        ("샘플 데이터 삽입", test_sample_data_insertion),
        ("복잡한 쿼리", test_complex_queries),
        ("데이터베이스 성능", test_database_performance),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n📋 {test_name} 테스트 실행 중...")
        if test_func():
            passed += 1
        else:
            logger.error(f"❌ {test_name} 테스트 실패")
    
    logger.info("=" * 60)
    logger.info(f"테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        logger.info("🎉 모든 테스트가 성공적으로 완료되었습니다!")
        return 0
    else:
        logger.error("⚠️  일부 테스트가 실패했습니다. 로그를 확인해주세요.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)