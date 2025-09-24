"""
회사 관리 엔드포인트
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from typing import Optional, List
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_user, require_analyst_or_admin
from app.core.logging import logger, log_api_call
from database.models import User, Company, NewsArticle, AlertRule

router = APIRouter()

@router.get("/", summary="회사 목록 조회")
@log_api_call
async def get_companies(
    skip: int = Query(0, ge=0, description="건너뛸 개수"),
    limit: int = Query(100, ge=1, le=1000, description="조회할 개수"),
    is_active: Optional[bool] = Query(None, description="활성 상태 필터"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """회사 목록 조회"""
    
    query = db.query(Company)
    
    if is_active is not None:
        query = query.filter(Company.is_active == is_active)
    
    companies = query.offset(skip).limit(limit).all()
    
    return [
        {
            "id": company.id,
            "name": company.name,
            "stock_code": company.stock_code,
            "industry": company.industry,
            "description": company.description,
            "website_url": company.website_url,
            "is_active": company.is_active,
            "created_at": company.created_at.isoformat(),
            "updated_at": company.updated_at.isoformat() if company.updated_at else None
        }
        for company in companies
    ]

@router.get("/{company_id}/news/recent", summary="회사 최근 뉴스")
@log_api_call
async def get_company_recent_news(
    company_id: int,
    limit: int = Query(10, ge=1, le=50, description="조회할 개수"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """회사의 최근 뉴스 조회"""
    
    # 회사 존재 확인
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다."
        )
    
    # 최근 뉴스 조회
    articles = db.query(NewsArticle).filter(
        NewsArticle.company_id == company_id
    ).order_by(desc(NewsArticle.published_date)).limit(limit).all()
    
    return [
        {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "source": article.source.value if article.source else None,
            "publishedAt": article.published_date.isoformat(),
            "sentiment": article.sentiment_score.value if article.sentiment_score else "neutral",
            "sentimentScore": _get_sentiment_numeric_score(article.sentiment_score),
            "stakeholderType": article.stakeholder_type.value if article.stakeholder_type else "unknown"
        }
        for article in articles
    ]

@router.get("/{company_id}/alerts", summary="회사 알림 조회")
@log_api_call
async def get_company_alerts(
    company_id: int,
    is_active: bool = Query(True, description="활성 알림만 조회"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """회사의 알림 조회"""
    
    # 회사 존재 확인
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다."
        )
    
    # 임시로 빈 배열 반환 (실제로는 AlertRule 테이블에서 조회)
    # TODO: 알림 시스템 구현 후 실제 데이터 반환
    return []

@router.get("/{company_id}/sentiment/trend", summary="회사 센티멘트 트렌드")
@log_api_call
async def get_company_sentiment_trend(
    company_id: int,
    stakeholder_type: Optional[str] = Query(None, description="스테이크홀더 타입"),
    time_range: str = Query("30d", description="기간 (7d, 30d, 90d)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """회사의 센티멘트 트렌드 조회"""
    
    # 회사 존재 확인
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다."
        )
    
    # 기간 계산
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(time_range, 30)
    start_date = datetime.now() - timedelta(days=days)
    
    # 쿼리 조건
    conditions = [
        NewsArticle.company_id == company_id,
        NewsArticle.published_date >= start_date
    ]
    
    if stakeholder_type:
        conditions.append(NewsArticle.stakeholder_type == stakeholder_type)
    
    # 일별 트렌드 데이터 생성
    trend_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        day_conditions = conditions + [
            func.date(NewsArticle.published_date) == date.date()
        ]
        
        avg_sentiment = db.query(
            func.avg(_get_sentiment_case_expression())
        ).filter(and_(*day_conditions)).scalar() or 0
        
        trend_data.append({
            "date": date_str,
            "sentiment": avg_sentiment
        })
    
    return trend_data

@router.get("/{company_id}/stakeholders/analysis", summary="회사 스테이크홀더 분석")
@log_api_call
async def get_company_stakeholder_analysis(
    company_id: int,
    time_range: str = Query("30d", description="기간 (7d, 30d, 90d)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """회사의 스테이크홀더별 분석 데이터 조회"""
    
    # 회사 존재 확인
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다."
        )
    
    # 기간 계산
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(time_range, 30)
    start_date = datetime.now() - timedelta(days=days)
    
    # 스테이크홀더별 분석
    stakeholder_analysis = db.query(
        NewsArticle.stakeholder_type,
        func.count(NewsArticle.id).label('count'),
        func.avg(_get_sentiment_case_expression()).label('avg_sentiment')
    ).filter(
        NewsArticle.company_id == company_id,
        NewsArticle.published_date >= start_date,
        NewsArticle.stakeholder_type.isnot(None)
    ).group_by(NewsArticle.stakeholder_type).all()
    
    return [
        {
            "name": result.stakeholder_type.value,
            "value": result.count,
            "sentiment": result.avg_sentiment or 0
        }
        for result in stakeholder_analysis
    ]

@router.get("/{company_id}/sentiment/distribution", summary="회사 센티멘트 분포")
@log_api_call
async def get_company_sentiment_distribution(
    company_id: int,
    stakeholder_type: Optional[str] = Query(None, description="스테이크홀더 타입"),
    time_range: str = Query("30d", description="기간 (7d, 30d, 90d)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """회사의 센티멘트 분포 조회"""
    
    # 회사 존재 확인
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회사를 찾을 수 없습니다."
        )
    
    # 기간 계산
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(time_range, 30)
    start_date = datetime.now() - timedelta(days=days)
    
    # 쿼리 조건
    conditions = [
        NewsArticle.company_id == company_id,
        NewsArticle.published_date >= start_date,
        NewsArticle.sentiment_score.isnot(None)
    ]
    
    if stakeholder_type:
        conditions.append(NewsArticle.stakeholder_type == stakeholder_type)
    
    # 전체 기사 수
    total_count = db.query(NewsArticle).filter(and_(*conditions)).count()
    
    # 센티멘트별 분포
    sentiment_distribution = db.query(
        NewsArticle.sentiment_score,
        func.count(NewsArticle.id).label('count')
    ).filter(and_(*conditions)).group_by(NewsArticle.sentiment_score).all()
    
    return [
        {
            "sentiment": result.sentiment_score.value,
            "count": result.count,
            "percentage": (result.count / total_count * 100) if total_count > 0 else 0
        }
        for result in sentiment_distribution
    ]

@router.post("/", summary="회사 생성")
@log_api_call
async def create_company(
    current_user: User = Depends(require_analyst_or_admin),
    db: Session = Depends(get_db)
):
    """회사 생성 (구현 예정)"""
    return {"message": "회사 생성 - 구현 예정"}

# 헬퍼 함수들
def _get_sentiment_numeric_score(sentiment_score):
    """센티멘트 점수를 숫자로 변환"""
    if not sentiment_score:
        return 0
    
    score_map = {
        "very_negative": -2,
        "negative": -1,
        "neutral": 0,
        "positive": 1,
        "very_positive": 2
    }
    return score_map.get(sentiment_score.value, 0)

def _get_sentiment_case_expression():
    """센티멘트 점수 계산을 위한 CASE 표현식"""
    from database.models import SentimentScore
    
    return func.case(
        (NewsArticle.sentiment_score == SentimentScore.VERY_NEGATIVE, -2),
        (NewsArticle.sentiment_score == SentimentScore.NEGATIVE, -1),
        (NewsArticle.sentiment_score == SentimentScore.NEUTRAL, 0),
        (NewsArticle.sentiment_score == SentimentScore.POSITIVE, 1),
        (NewsArticle.sentiment_score == SentimentScore.VERY_POSITIVE, 2),
        else_=0
    )