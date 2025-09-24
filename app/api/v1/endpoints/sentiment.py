"""
센티멘트 분석 엔드포인트
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc
from celery.result import AsyncResult

from app.core.database import get_db
from app.core.security import get_current_user, require_analyst_or_admin
from app.core.logging import logger, log_api_call
from app.ml.analysis_manager import get_analysis_manager
from app.tasks.analysis_tasks import (
    analyze_pending_articles_task,
    analyze_single_article_task,
    test_analysis_task,
    get_analysis_statistics_task
)
from app.schemas.base import ResponseSchema
from database.models import (
    User, NewsArticle, SentimentTrend, Company,
    SentimentScore, StakeholderType
)

router = APIRouter()


@router.get("/trends", summary="센티멘트 트렌드 조회")
@log_api_call
async def get_sentiment_trends(
    company_id: Optional[int] = Query(None, description="회사 ID"),
    stakeholder_type: Optional[StakeholderType] = Query(None, description="스테이크홀더 타입"),
    days: int = Query(30, ge=1, le=365, description="조회 기간 (일)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    센티멘트 트렌드 조회
    
    - **company_id**: 특정 회사 ID (선택사항)
    - **stakeholder_type**: 스테이크홀더 타입 (선택사항)
    - **days**: 조회 기간 (기본값: 30일)
    """
    try:
        # 날짜 범위 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 쿼리 구성
        query = db.query(SentimentTrend).filter(
            and_(
                SentimentTrend.date >= start_date,
                SentimentTrend.date <= end_date
            )
        )
        
        # 필터 적용
        if company_id:
            query = query.filter(SentimentTrend.company_id == company_id)
        
        if stakeholder_type:
            query = query.filter(SentimentTrend.stakeholder_type == stakeholder_type)
        
        # 결과 조회
        trends = query.order_by(desc(SentimentTrend.date)).all()
        
        # 회사 정보 조회 (필요한 경우)
        company_info = {}
        if trends:
            company_ids = list(set(trend.company_id for trend in trends))
            companies = db.query(Company).filter(Company.id.in_(company_ids)).all()
            company_info = {company.id: company.name for company in companies}
        
        # 응답 데이터 구성
        trend_data = []
        for trend in trends:
            trend_data.append({
                "date": trend.date.isoformat(),
                "company_id": trend.company_id,
                "company_name": company_info.get(trend.company_id, "Unknown"),
                "stakeholder_type": trend.stakeholder_type.value,
                "total_articles": trend.total_articles,
                "positive_count": trend.positive_count,
                "negative_count": trend.negative_count,
                "neutral_count": trend.neutral_count,
                "avg_sentiment_score": trend.avg_sentiment_score,
                "sentiment_volatility": trend.sentiment_volatility,
                "top_keywords": trend.top_keywords
            })
        
        return ResponseSchema(
            success=True,
            message="센티멘트 트렌드 조회 완료",
            data={
                "trends": trend_data,
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "filters": {
                    "company_id": company_id,
                    "stakeholder_type": stakeholder_type.value if stakeholder_type else None
                },
                "total_trends": len(trend_data)
            }
        )
        
    except Exception as e:
        logger.error(f"센티멘트 트렌드 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"트렌드 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/analyze", summary="센티멘트 분석 시작")
@log_api_call
async def start_sentiment_analysis(
    limit: int = Query(100, ge=1, le=1000, description="분석할 최대 기사 수"),
    current_user: User = Depends(require_analyst_or_admin),
):
    """
    대기 중인 기사들의 센티멘트 분석 시작
    
    - **limit**: 분석할 최대 기사 수 (기본값: 100개)
    """
    try:
        logger.info(f"센티멘트 분석 시작 요청 (사용자: {current_user.email}, 제한: {limit}개)")
        
        # Celery 작업 시작
        task = analyze_pending_articles_task.delay(limit=limit)
        
        logger.info(f"센티멘트 분석 작업 시작됨 - Task ID: {task.id}")
        
        return ResponseSchema(
            success=True,
            message="센티멘트 분석이 시작되었습니다",
            data={
                "task_id": task.id,
                "limit": limit,
                "status": "started",
                "message": "백그라운드에서 분석이 진행됩니다. 상태는 /sentiment/status/{task_id}에서 확인할 수 있습니다."
            }
        )
        
    except Exception as e:
        logger.error(f"센티멘트 분석 시작 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분석 시작 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/analyze/{article_id}", summary="단일 기사 센티멘트 분석")
@log_api_call
async def analyze_single_article(
    article_id: int,
    current_user: User = Depends(require_analyst_or_admin),
    db: Session = Depends(get_db)
):
    """
    특정 기사의 센티멘트 분석
    
    - **article_id**: 분석할 기사 ID
    """
    try:
        # 기사 존재 확인
        article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
        if not article:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="기사를 찾을 수 없습니다"
            )
        
        logger.info(f"단일 기사 분석 요청 (ID: {article_id}, 사용자: {current_user.email})")
        
        # Celery 작업 시작
        task = analyze_single_article_task.delay(article_id=article_id)
        
        logger.info(f"단일 기사 분석 작업 시작됨 - Task ID: {task.id}")
        
        return ResponseSchema(
            success=True,
            message=f"기사 {article_id} 센티멘트 분석이 시작되었습니다",
            data={
                "task_id": task.id,
                "article_id": article_id,
                "article_title": article.title,
                "status": "started"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"단일 기사 분석 시작 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분석 시작 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/status/{task_id}", summary="분석 작업 상태 조회")
@log_api_call
async def get_analysis_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    센티멘트 분석 작업 상태 조회
    
    - **task_id**: 작업 ID
    """
    try:
        # Celery 작업 결과 조회
        task_result = AsyncResult(task_id)
        
        if task_result.state == "PENDING":
            response = {
                "task_id": task_id,
                "status": "pending",
                "message": "작업이 대기 중입니다"
            }
        elif task_result.state == "PROGRESS":
            response = {
                "task_id": task_id,
                "status": "progress",
                "message": "작업이 진행 중입니다",
                "meta": task_result.info
            }
        elif task_result.state == "SUCCESS":
            response = {
                "task_id": task_id,
                "status": "success",
                "message": "작업이 완료되었습니다",
                "result": task_result.result
            }
        elif task_result.state == "FAILURE":
            response = {
                "task_id": task_id,
                "status": "failure",
                "message": "작업이 실패했습니다",
                "error": str(task_result.info)
            }
        else:
            response = {
                "task_id": task_id,
                "status": task_result.state.lower(),
                "message": f"작업 상태: {task_result.state}"
            }
        
        return ResponseSchema(
            success=True,
            message="작업 상태 조회 완료",
            data=response
        )
        
    except Exception as e:
        logger.error(f"분석 작업 상태 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작업 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/statistics", summary="센티멘트 분석 통계")
@log_api_call
async def get_sentiment_statistics(
    days: int = Query(30, ge=1, le=365, description="조회 기간 (일)"),
    current_user: User = Depends(get_current_user)
):
    """
    센티멘트 분석 통계 조회
    
    - **days**: 조회 기간 (기본값: 30일)
    """
    try:
        # Celery 작업으로 통계 조회
        task = get_analysis_statistics_task.delay(days=days)
        statistics = task.get(timeout=10)  # 10초 타임아웃
        
        return ResponseSchema(
            success=True,
            message="센티멘트 분석 통계 조회 완료",
            data=statistics
        )
        
    except Exception as e:
        logger.error(f"센티멘트 분석 통계 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/distribution", summary="센티멘트 분포 조회")
@log_api_call
async def get_sentiment_distribution(
    company_id: Optional[int] = Query(None, description="회사 ID"),
    days: int = Query(30, ge=1, le=365, description="조회 기간 (일)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    센티멘트 분포 조회
    
    - **company_id**: 특정 회사 ID (선택사항)
    - **days**: 조회 기간 (기본값: 30일)
    """
    try:
        # 날짜 범위 설정
        since_date = datetime.now() - timedelta(days=days)
        
        # 쿼리 구성
        query = db.query(NewsArticle).filter(
            and_(
                NewsArticle.published_date >= since_date,
                NewsArticle.sentiment_score.isnot(None)
            )
        )
        
        if company_id:
            query = query.filter(NewsArticle.company_id == company_id)
        
        # 센티멘트별 분포
        sentiment_counts = {}
        for sentiment in SentimentScore:
            count = query.filter(NewsArticle.sentiment_score == sentiment).count()
            sentiment_counts[sentiment.value] = count
        
        # 스테이크홀더별 분포
        stakeholder_counts = {}
        for stakeholder in StakeholderType:
            count = query.filter(NewsArticle.stakeholder_type == stakeholder).count()
            stakeholder_counts[stakeholder.value] = count
        
        # 전체 통계
        total_articles = query.count()
        avg_confidence = db.query(func.avg(NewsArticle.sentiment_confidence)).filter(
            and_(
                NewsArticle.published_date >= since_date,
                NewsArticle.sentiment_confidence.isnot(None)
            )
        ).scalar() or 0
        
        return ResponseSchema(
            success=True,
            message="센티멘트 분포 조회 완료",
            data={
                "period": {
                    "days": days,
                    "start_date": since_date.isoformat(),
                    "end_date": datetime.now().isoformat()
                },
                "total_articles": total_articles,
                "avg_confidence": round(float(avg_confidence), 3),
                "sentiment_distribution": sentiment_counts,
                "stakeholder_distribution": stakeholder_counts,
                "company_id": company_id
            }
        )
        
    except Exception as e:
        logger.error(f"센티멘트 분포 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분포 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/test", summary="센티멘트 분석 테스트")
@log_api_call
async def test_sentiment_analysis(
    test_text: str = Query("삼성전자의 새로운 제품이 출시되어 고객들의 반응이 좋습니다.", description="테스트할 텍스트"),
    current_user: User = Depends(require_analyst_or_admin)
):
    """
    센티멘트 분석 기능 테스트
    
    - **test_text**: 테스트할 텍스트
    """
    try:
        logger.info(f"센티멘트 분석 테스트 시작 (사용자: {current_user.email})")
        
        # Celery 테스트 작업 시작
        task = test_analysis_task.delay(test_text=test_text)
        
        return ResponseSchema(
            success=True,
            message="센티멘트 분석 테스트가 시작되었습니다",
            data={
                "task_id": task.id,
                "test_text": test_text,
                "status": "started",
                "message": "테스트 결과는 /sentiment/status/{task_id}에서 확인할 수 있습니다."
            }
        )
        
    except Exception as e:
        logger.error(f"센티멘트 분석 테스트 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"테스트 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/models", summary="사용 가능한 분석 모델 정보")
@log_api_call
async def get_analysis_models(
    current_user: User = Depends(get_current_user)
):
    """
    사용 가능한 센티멘트 분석 모델 정보 조회
    """
    try:
        manager = get_analysis_manager()
        model_info = manager.analyzer.get_model_info()
        
        return ResponseSchema(
            success=True,
            message="분석 모델 정보 조회 완료",
            data={
                "current_model": model_info,
                "supported_sentiments": [sentiment.value for sentiment in SentimentScore],
                "supported_stakeholders": [stakeholder.value for stakeholder in StakeholderType],
                "analysis_features": [
                    "한국어 특화 BERT 모델",
                    "키워드 기반 분석",
                    "스테이크홀더 자동 분류",
                    "신뢰도 점수 제공",
                    "배치 분석 지원"
                ]
            }
        )
        
    except Exception as e:
        logger.error(f"분석 모델 정보 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"모델 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )