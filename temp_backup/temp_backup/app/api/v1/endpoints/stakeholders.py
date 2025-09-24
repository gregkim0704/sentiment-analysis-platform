"""
스테이크홀더 분석 엔드포인트
"""

from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user, require_analyst_or_admin
from app.core.logging import logger, log_api_call
from app.stakeholders.stakeholder_manager import get_stakeholder_manager
from app.schemas.base import ResponseSchema
from database.models import User, Company, StakeholderType

router = APIRouter()


@router.get("/types", summary="스테이크홀더 타입 목록")
@log_api_call
async def get_stakeholder_types(
    current_user: User = Depends(get_current_user)
):
    """
    사용 가능한 스테이크홀더 타입 목록 조회
    """
    try:
        manager = get_stakeholder_manager()
        stakeholders = manager.get_available_stakeholders()
        
        return ResponseSchema(
            success=True,
            message="스테이크홀더 타입 목록 조회 완료",
            data={
                "stakeholders": stakeholders,
                "total_types": len(stakeholders),
                "available_analyzers": len([s for s in stakeholders if s["analyzer_available"]])
            }
        )
        
    except Exception as e:
        logger.error(f"스테이크홀더 타입 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"스테이크홀더 타입 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/insights/{company_id}", summary="스테이크홀더 인사이트 분석")
@log_api_call
async def get_stakeholder_insights(
    company_id: int,
    stakeholder_type: Optional[StakeholderType] = Query(None, description="특정 스테이크홀더 타입"),
    days: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    스테이크홀더별 인사이트 분석
    
    - **company_id**: 분석할 회사 ID
    - **stakeholder_type**: 특정 스테이크홀더 타입 (선택사항)
    - **days**: 분석 기간 (기본값: 30일)
    """
    try:
        # 회사 존재 확인
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="회사를 찾을 수 없습니다"
            )
        
        logger.info(f"스테이크홀더 인사이트 분석 요청 (회사: {company.name}, 사용자: {current_user.email})")
        
        # 스테이크홀더 분석 실행
        manager = get_stakeholder_manager()
        result = await manager.analyze_stakeholder_insights(
            company_id, stakeholder_type, days, db
        )
        
        if result.get("success"):
            return ResponseSchema(
                success=True,
                message="스테이크홀더 인사이트 분석 완료",
                data=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "분석 중 오류가 발생했습니다")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스테이크홀더 인사이트 분석 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"인사이트 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/comparison/{company_id}", summary="스테이크홀더 간 비교 분석")
@log_api_call
async def get_stakeholder_comparison(
    company_id: int,
    days: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    스테이크홀더 간 비교 분석
    
    - **company_id**: 분석할 회사 ID
    - **days**: 분석 기간 (기본값: 30일)
    """
    try:
        # 회사 존재 확인
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="회사를 찾을 수 없습니다"
            )
        
        logger.info(f"스테이크홀더 비교 분석 요청 (회사: {company.name}, 사용자: {current_user.email})")
        
        # 비교 분석 실행
        manager = get_stakeholder_manager()
        result = await manager.get_stakeholder_comparison(company_id, days, db)
        
        if result.get("success"):
            return ResponseSchema(
                success=True,
                message="스테이크홀더 비교 분석 완료",
                data=result
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "비교 분석 중 오류가 발생했습니다")
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"스테이크홀더 비교 분석 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"비교 분석 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/summary", summary="전체 스테이크홀더 요약")
@log_api_call
async def get_stakeholder_summary(
    days: int = Query(30, ge=1, le=365, description="분석 기간 (일)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    전체 스테이크홀더 요약 정보
    
    - **days**: 분석 기간 (기본값: 30일)
    """
    try:
        from datetime import datetime, timedelta
        from sqlalchemy import func, and_
        
        # 날짜 범위 설정
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 스테이크홀더별 기사 수 통계
        stakeholder_stats = {}
        
        for stakeholder_type in StakeholderType:
            # 기사 수 조회
            article_count = db.query(func.count(NewsArticle.id)).filter(
                and_(
                    NewsArticle.stakeholder_type == stakeholder_type,
                    NewsArticle.published_date >= start_date,
                    NewsArticle.published_date <= end_date,
                    NewsArticle.sentiment_score.isnot(None)
                )
            ).scalar() or 0
            
            # 평균 센티멘트 조회
            avg_sentiment = db.query(func.avg(
                func.case(
                    (NewsArticle.sentiment_score == 'very_negative', -2),
                    (NewsArticle.sentiment_score == 'negative', -1),
                    (NewsArticle.sentiment_score == 'neutral', 0),
                    (NewsArticle.sentiment_score == 'positive', 1),
                    (NewsArticle.sentiment_score == 'very_positive', 2),
                    else_=0
                )
            )).filter(
                and_(
                    NewsArticle.stakeholder_type == stakeholder_type,
                    NewsArticle.published_date >= start_date,
                    NewsArticle.published_date <= end_date,
                    NewsArticle.sentiment_score.isnot(None)
                )
            ).scalar() or 0.0
            
            stakeholder_stats[stakeholder_type.value] = {
                "article_count": article_count,
                "avg_sentiment": round(float(avg_sentiment), 3),
                "has_analyzer": stakeholder_type in get_stakeholder_manager().analyzers
            }
        
        # 전체 통계
        total_articles = sum(stats["article_count"] for stats in stakeholder_stats.values())
        active_stakeholders = len([stats for stats in stakeholder_stats.values() if stats["article_count"] > 0])
        
        # 가장 활발한 스테이크홀더
        most_active = max(
            stakeholder_stats.items(), 
            key=lambda x: x[1]["article_count"]
        ) if stakeholder_stats else None
        
        return ResponseSchema(
            success=True,
            message="스테이크홀더 요약 조회 완료",
            data={
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "summary": {
                    "total_articles": total_articles,
                    "active_stakeholders": active_stakeholders,
                    "total_stakeholder_types": len(StakeholderType),
                    "most_active_stakeholder": most_active[0] if most_active else None,
                    "most_active_count": most_active[1]["article_count"] if most_active else 0
                },
                "stakeholder_stats": stakeholder_stats,
                "available_analyzers": len(get_stakeholder_manager().analyzers)
            }
        )
        
    except Exception as e:
        logger.error(f"스테이크홀더 요약 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"요약 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/action-items/{company_id}", summary="스테이크홀더별 액션 아이템")
@log_api_call
async def get_stakeholder_action_items(
    company_id: int,
    urgency_filter: Optional[str] = Query(None, description="긴급도 필터 (low, medium, high, critical)"),
    current_user: User = Depends(require_analyst_or_admin),
    db: Session = Depends(get_db)
):
    """
    스테이크홀더별 권장 액션 아이템 조회
    
    - **company_id**: 회사 ID
    - **urgency_filter**: 긴급도 필터 (선택사항)
    """
    try:
        # 회사 존재 확인
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="회사를 찾을 수 없습니다"
            )
        
        # 스테이크홀더 인사이트 분석
        manager = get_stakeholder_manager()
        insights_result = await manager.analyze_stakeholder_insights(company_id, None, 30, db)
        
        if not insights_result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="인사이트 분석에 실패했습니다"
            )
        
        # 액션 아이템 추출 및 필터링
        action_items = {}
        urgent_actions = []
        
        for stakeholder_type, insight in insights_result["insights"].items():
            if "error" in insight:
                continue
            
            # 긴급도 필터 적용
            if urgency_filter and insight.get("urgency_level") != urgency_filter:
                continue
            
            actions = insight.get("action_items", [])
            if actions:
                action_items[stakeholder_type] = {
                    "urgency_level": insight.get("urgency_level"),
                    "impact_level": insight.get("impact_level"),
                    "sentiment_score": insight.get("sentiment_score"),
                    "action_items": actions,
                    "key_concerns": insight.get("key_concerns", [])
                }
                
                # 긴급한 액션 아이템 별도 수집
                if insight.get("urgency_level") in ["high", "critical"]:
                    for action in actions:
                        urgent_actions.append({
                            "stakeholder": stakeholder_type,
                            "action": action,
                            "urgency": insight.get("urgency_level"),
                            "impact": insight.get("impact_level")
                        })
        
        return ResponseSchema(
            success=True,
            message="스테이크홀더 액션 아이템 조회 완료",
            data={
                "company_id": company_id,
                "company_name": company.name,
                "action_items": action_items,
                "urgent_actions": urgent_actions,
                "total_stakeholders": len(action_items),
                "urgent_count": len(urgent_actions),
                "urgency_filter": urgency_filter
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"액션 아이템 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"액션 아이템 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/analyzer-info/{stakeholder_type}", summary="스테이크홀더 분석기 정보")
@log_api_call
async def get_analyzer_info(
    stakeholder_type: StakeholderType,
    current_user: User = Depends(get_current_user)
):
    """
    특정 스테이크홀더 분석기 상세 정보
    
    - **stakeholder_type**: 스테이크홀더 타입
    """
    try:
        manager = get_stakeholder_manager()
        
        if stakeholder_type in manager.analyzers:
            analyzer = manager.analyzers[stakeholder_type]
            info = analyzer.get_stakeholder_info()
            
            # 키워드 정보 추가
            keywords = analyzer.get_specific_keywords()
            info["keywords"] = keywords
            
            return ResponseSchema(
                success=True,
                message="분석기 정보 조회 완료",
                data=info
            )
        else:
            return ResponseSchema(
                success=True,
                message="기본 분석기 사용",
                data={
                    "type": stakeholder_type.value,
                    "name": stakeholder_type.value,
                    "description": "기본 분석기를 사용합니다",
                    "analyzer_available": False,
                    "key_metrics": ["기본 센티멘트 지표"],
                    "keywords": {}
                }
            )
        
    except Exception as e:
        logger.error(f"분석기 정보 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"분석기 정보 조회 중 오류가 발생했습니다: {str(e)}"
        )