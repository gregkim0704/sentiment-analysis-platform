"""
대시보드 엔드포인트
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from typing import Optional, List
from datetime import datetime, timedelta
from app.core.database import get_db
from app.core.security import get_current_user
from app.core.logging import log_api_call
from database.models import User, Company, NewsArticle, SentimentTrend, StakeholderType, SentimentScore

router = APIRouter()

@router.get("", summary="대시보드 데이터")
@log_api_call
async def get_dashboard_data(
    company_id: Optional[int] = Query(None, description="회사 ID"),
    stakeholder_type: Optional[StakeholderType] = Query(None, description="스테이크홀더 타입"),
    time_range: str = Query("30d", description="기간 (7d, 30d, 90d)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """대시보드 메인 데이터 조회"""
    
    # 기간 계산
    days_map = {"7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(time_range, 30)
    start_date = datetime.now() - timedelta(days=days)
    
    # 기본 쿼리 조건
    query_conditions = [NewsArticle.published_date >= start_date]
    if company_id:
        query_conditions.append(NewsArticle.company_id == company_id)
    if stakeholder_type:
        query_conditions.append(NewsArticle.stakeholder_type == stakeholder_type)
    
    # 전체 센티멘트 점수 계산
    overall_sentiment_query = db.query(
        func.avg(
            func.case(
                (NewsArticle.sentiment_score == SentimentScore.VERY_NEGATIVE, -2),
                (NewsArticle.sentiment_score == SentimentScore.NEGATIVE, -1),
                (NewsArticle.sentiment_score == SentimentScore.NEUTRAL, 0),
                (NewsArticle.sentiment_score == SentimentScore.POSITIVE, 1),
                (NewsArticle.sentiment_score == SentimentScore.VERY_POSITIVE, 2),
                else_=0
            )
        )
    ).filter(and_(*query_conditions))
    
    overall_sentiment = overall_sentiment_query.scalar() or 0
    
    # 총 기사 수
    total_articles = db.query(NewsArticle).filter(and_(*query_conditions)).count()
    
    # 오늘 기사 수
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    today_conditions = query_conditions + [NewsArticle.published_date >= today_start]
    today_articles = db.query(NewsArticle).filter(and_(*today_conditions)).count()
    
    # 활성 스테이크홀더 수
    active_stakeholders = db.query(NewsArticle.stakeholder_type).filter(
        and_(*query_conditions)
    ).distinct().count()
    
    # 활성 알림 수 (임시로 0)
    active_alerts = 0
    
    # 트렌드 데이터 생성
    trend_data = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        
        # 해당 날짜의 데이터 조회
        day_conditions = query_conditions + [
            func.date(NewsArticle.published_date) == date.date()
        ]
        
        # 전체 평균
        overall_avg = db.query(
            func.avg(
                func.case(
                    (NewsArticle.sentiment_score == SentimentScore.VERY_NEGATIVE, -2),
                    (NewsArticle.sentiment_score == SentimentScore.NEGATIVE, -1),
                    (NewsArticle.sentiment_score == SentimentScore.NEUTRAL, 0),
                    (NewsArticle.sentiment_score == SentimentScore.POSITIVE, 1),
                    (NewsArticle.sentiment_score == SentimentScore.VERY_POSITIVE, 2),
                    else_=0
                )
            )
        ).filter(and_(*day_conditions)).scalar() or 0
        
        # 스테이크홀더별 평균
        stakeholder_avgs = {}
        for st_type in [StakeholderType.CUSTOMER, StakeholderType.INVESTOR, 
                       StakeholderType.EMPLOYEE, StakeholderType.MEDIA]:
            st_conditions = day_conditions + [NewsArticle.stakeholder_type == st_type]
            avg = db.query(
                func.avg(
                    func.case(
                        (NewsArticle.sentiment_score == SentimentScore.VERY_NEGATIVE, -2),
                        (NewsArticle.sentiment_score == SentimentScore.NEGATIVE, -1),
                        (NewsArticle.sentiment_score == SentimentScore.NEUTRAL, 0),
                        (NewsArticle.sentiment_score == SentimentScore.POSITIVE, 1),
                        (NewsArticle.sentiment_score == SentimentScore.VERY_POSITIVE, 2),
                        else_=0
                    )
                )
            ).filter(and_(*st_conditions)).scalar() or 0
            stakeholder_avgs[st_type.value] = avg
        
        trend_data.append({
            "date": date_str,
            "overall": overall_avg,
            "customer": stakeholder_avgs.get("customer", 0),
            "investor": stakeholder_avgs.get("investor", 0),
            "employee": stakeholder_avgs.get("employee", 0),
            "media": stakeholder_avgs.get("media", 0)
        })
    
    # 스테이크홀더별 데이터
    stakeholder_data = []
    for st_type in StakeholderType:
        st_conditions = query_conditions + [NewsArticle.stakeholder_type == st_type]
        count = db.query(NewsArticle).filter(and_(*st_conditions)).count()
        
        if count > 0:
            avg_sentiment = db.query(
                func.avg(
                    func.case(
                        (NewsArticle.sentiment_score == SentimentScore.VERY_NEGATIVE, -2),
                        (NewsArticle.sentiment_score == SentimentScore.NEGATIVE, -1),
                        (NewsArticle.sentiment_score == SentimentScore.NEUTRAL, 0),
                        (NewsArticle.sentiment_score == SentimentScore.POSITIVE, 1),
                        (NewsArticle.sentiment_score == SentimentScore.VERY_POSITIVE, 2),
                        else_=0
                    )
                )
            ).filter(and_(*st_conditions)).scalar() or 0
            
            stakeholder_data.append({
                "name": st_type.value,
                "value": count,
                "sentiment": avg_sentiment
            })
    
    # 센티멘트 분포
    sentiment_distribution = []
    for sentiment in SentimentScore:
        sent_conditions = query_conditions + [NewsArticle.sentiment_score == sentiment]
        count = db.query(NewsArticle).filter(and_(*sent_conditions)).count()
        percentage = (count / total_articles * 100) if total_articles > 0 else 0
        
        sentiment_distribution.append({
            "sentiment": sentiment.value,
            "count": count,
            "percentage": percentage
        })
    
    return {
        "overallSentiment": overall_sentiment,
        "totalArticles": total_articles,
        "todayArticles": today_articles,
        "activeStakeholders": active_stakeholders,
        "activeAlerts": active_alerts,
        "trendData": trend_data,
        "stakeholderData": stakeholder_data,
        "sentimentDistribution": sentiment_distribution
    }

@router.get("/overview", summary="대시보드 개요")
@log_api_call
async def get_dashboard_overview(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """대시보드 개요 조회"""
    
    # 기본 통계
    total_companies = db.query(Company).filter(Company.is_active == True).count()
    total_articles = db.query(NewsArticle).count()
    
    # 최근 30일 기사 수
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_articles = db.query(NewsArticle).filter(
        NewsArticle.published_date >= thirty_days_ago
    ).count()
    
    # 분석된 기사 수
    analyzed_articles = db.query(NewsArticle).filter(
        NewsArticle.sentiment_score.isnot(None)
    ).count()
    
    return {
        "totalCompanies": total_companies,
        "totalArticles": total_articles,
        "recentArticles": recent_articles,
        "analyzedArticles": analyzed_articles,
        "analysisRate": (analyzed_articles / total_articles * 100) if total_articles > 0 else 0
    }