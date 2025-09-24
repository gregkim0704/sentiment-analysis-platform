"""
스테이크홀더 분석 매니저
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, desc

from app.stakeholders.base_stakeholder import (
    BaseStakeholderAnalyzer, 
    StakeholderInsight, 
    StakeholderTrend,
    ImpactLevel,
    UrgencyLevel
)
from app.stakeholders.customer_analyzer import CustomerAnalyzer
from app.stakeholders.investor_analyzer import InvestorAnalyzer
from app.stakeholders.employee_analyzer import EmployeeAnalyzer
from app.stakeholders.government_analyzer import GovernmentAnalyzer
from app.stakeholders.media_analyzer import MediaAnalyzer
from app.core.database import get_db
from app.core.logging import logger
from database.models import (
    NewsArticle, Company, SentimentTrend,
    StakeholderType, SentimentScore
)


class StakeholderAnalysisManager:
    """스테이크홀더 분석 매니저"""
    
    def __init__(self):
        # 스테이크홀더별 분석기 등록
        self.analyzers: Dict[StakeholderType, BaseStakeholderAnalyzer] = {
            StakeholderType.CUSTOMER: CustomerAnalyzer(),
            StakeholderType.INVESTOR: InvestorAnalyzer(),
            StakeholderType.EMPLOYEE: EmployeeAnalyzer(),
            StakeholderType.GOVERNMENT: GovernmentAnalyzer(),
            StakeholderType.MEDIA: MediaAnalyzer(),
        }
        
        # 나머지 스테이크홀더는 기본 분석기 사용 (향후 확장)
        # StakeholderType.PARTNER: PartnerAnalyzer(),
        # StakeholderType.COMPETITOR: CompetitorAnalyzer(),
        # StakeholderType.COMMUNITY: CommunityAnalyzer(),
    
    def get_available_stakeholders(self) -> List[Dict[str, Any]]:
        """사용 가능한 스테이크홀더 목록 반환"""
        stakeholders = []
        
        for stakeholder_type, analyzer in self.analyzers.items():
            stakeholders.append({
                "type": stakeholder_type.value,
                "name": analyzer.name,
                "description": analyzer.get_description(),
                "key_metrics": analyzer.get_key_metrics(),
                "analyzer_available": True
            })
        
        # 분석기가 없는 스테이크홀더들도 포함
        for stakeholder_type in StakeholderType:
            if stakeholder_type not in self.analyzers:
                stakeholders.append({
                    "type": stakeholder_type.value,
                    "name": stakeholder_type.value,
                    "description": "기본 분석기 사용",
                    "key_metrics": ["기본 센티멘트 지표"],
                    "analyzer_available": False
                })
        
        return stakeholders
    
    async def analyze_stakeholder_insights(
        self, 
        company_id: int,
        stakeholder_type: Optional[StakeholderType] = None,
        days: int = 30,
        db: Session = None
    ) -> Dict[str, Any]:
        """스테이크홀더 인사이트 분석"""
        
        if db is None:
            db = next(get_db())
            should_close_db = True
        else:
            should_close_db = False
        
        try:
            logger.info(f"스테이크홀더 인사이트 분석 시작 (회사 ID: {company_id})")
            
            # 회사 정보 조회
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                return {
                    "success": False,
                    "error": "회사를 찾을 수 없습니다"
                }
            
            # 날짜 범위 설정
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            # 분석할 스테이크홀더 결정
            target_stakeholders = [stakeholder_type] if stakeholder_type else list(self.analyzers.keys())
            
            insights = {}
            
            for stakeholder in target_stakeholders:
                try:
                    # 해당 스테이크홀더의 기사 데이터 조회
                    articles_data = self._get_stakeholder_articles(
                        db, company_id, stakeholder, start_date, end_date
                    )
                    
                    # 트렌드 데이터 조회
                    trend_data = self._get_stakeholder_trend(
                        db, company_id, stakeholder, days
                    )
                    
                    # 분석기가 있는 경우 상세 분석
                    if stakeholder in self.analyzers:
                        analyzer = self.analyzers[stakeholder]
                        insight = analyzer.analyze_stakeholder_insight(articles_data, trend_data)
                        insights[stakeholder.value] = insight.to_dict()
                    else:
                        # 기본 분석
                        basic_insight = self._create_basic_insight(
                            stakeholder, articles_data, trend_data
                        )
                        insights[stakeholder.value] = basic_insight
                    
                except Exception as e:
                    logger.error(f"스테이크홀더 분석 오류 ({stakeholder.value}): {e}")
                    insights[stakeholder.value] = {
                        "error": str(e),
                        "stakeholder_type": stakeholder.value
                    }
            
            return {
                "success": True,
                "company_id": company_id,
                "company_name": company.name,
                "analysis_period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": days
                },
                "insights": insights,
                "analyzed_stakeholders": len(insights),
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"스테이크홀더 인사이트 분석 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if should_close_db:
                db.close()
    
    def _get_stakeholder_articles(
        self, 
        db: Session, 
        company_id: int, 
        stakeholder_type: StakeholderType,
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict]:
        """스테이크홀더별 기사 데이터 조회"""
        
        articles = db.query(NewsArticle).filter(
            and_(
                NewsArticle.company_id == company_id,
                NewsArticle.stakeholder_type == stakeholder_type,
                NewsArticle.published_date >= start_date,
                NewsArticle.published_date <= end_date,
                NewsArticle.sentiment_score.isnot(None)
            )
        ).all()
        
        articles_data = []
        for article in articles:
            articles_data.append({
                "id": article.id,
                "title": article.title,
                "content": article.content,
                "url": article.url,
                "author": article.author,
                "published_date": article.published_date.isoformat(),
                "sentiment_score": article.sentiment_score.value,
                "sentiment_confidence": article.sentiment_confidence,
                "keywords": article.keywords or [],
                "source": article.source.value if article.source else None
            })
        
        return articles_data
    
    def _get_stakeholder_trend(
        self, 
        db: Session, 
        company_id: int, 
        stakeholder_type: StakeholderType,
        days: int
    ) -> Dict[str, Any]:
        """스테이크홀더 트렌드 데이터 조회"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 트렌드 데이터 조회
        trends = db.query(SentimentTrend).filter(
            and_(
                SentimentTrend.company_id == company_id,
                SentimentTrend.stakeholder_type == stakeholder_type,
                SentimentTrend.date >= start_date,
                SentimentTrend.date <= end_date
            )
        ).order_by(SentimentTrend.date).all()
        
        if not trends:
            return {
                "sentiment_change": 0.0,
                "volume_change": 0.0,
                "avg_sentiment": 0.0,
                "total_articles": 0
            }
        
        # 변화율 계산
        first_sentiment = trends[0].avg_sentiment_score or 0
        last_sentiment = trends[-1].avg_sentiment_score or 0
        sentiment_change = ((last_sentiment - first_sentiment) / max(abs(first_sentiment), 0.1)) * 100
        
        first_volume = trends[0].total_articles or 0
        last_volume = trends[-1].total_articles or 0
        volume_change = ((last_volume - first_volume) / max(first_volume, 1)) * 100
        
        # 평균 센티멘트
        avg_sentiment = sum(trend.avg_sentiment_score or 0 for trend in trends) / len(trends)
        
        # 총 기사 수
        total_articles = sum(trend.total_articles or 0 for trend in trends)
        
        return {
            "sentiment_change": sentiment_change,
            "volume_change": volume_change,
            "avg_sentiment": avg_sentiment,
            "total_articles": total_articles,
            "trend_count": len(trends)
        }
    
    def _create_basic_insight(
        self, 
        stakeholder_type: StakeholderType,
        articles_data: List[Dict],
        trend_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """기본 인사이트 생성 (분석기가 없는 스테이크홀더용)"""
        
        if not articles_data:
            return {
                "stakeholder_type": stakeholder_type.value,
                "sentiment_score": "neutral",
                "confidence": 0.0,
                "impact_level": "very_low",
                "urgency_level": "low",
                "key_concerns": [],
                "positive_factors": [],
                "negative_factors": [],
                "action_items": ["데이터 부족으로 분석 불가"],
                "analysis_date": datetime.now().isoformat(),
                "article_count": 0,
                "keywords": [],
                "reasoning": "기본 분석기 사용"
            }
        
        # 기본 통계 계산
        sentiments = [self._sentiment_to_numeric(article.get('sentiment_score', 'neutral')) 
                     for article in articles_data]
        avg_sentiment = sum(sentiments) / len(sentiments)
        confidence = sum(article.get('sentiment_confidence', 0.0) for article in articles_data) / len(articles_data)
        
        # 센티멘트 점수를 enum으로 변환
        sentiment_enum = self._numeric_to_sentiment(avg_sentiment)
        
        # 기본 영향도 및 긴급도 계산
        impact_level = self._calculate_basic_impact(len(articles_data), abs(avg_sentiment))
        urgency_level = self._calculate_basic_urgency(avg_sentiment, impact_level)
        
        # 키워드 추출
        all_keywords = []
        for article in articles_data:
            if article.get('keywords'):
                all_keywords.extend(article['keywords'])
        
        from collections import Counter
        top_keywords = [word for word, count in Counter(all_keywords).most_common(5)]
        
        return {
            "stakeholder_type": stakeholder_type.value,
            "sentiment_score": sentiment_enum.value,
            "confidence": confidence,
            "impact_level": impact_level.value,
            "urgency_level": urgency_level.value,
            "key_concerns": ["기본 분석"],
            "positive_factors": ["긍정적 언급"] if avg_sentiment > 0 else [],
            "negative_factors": ["부정적 언급"] if avg_sentiment < 0 else [],
            "action_items": ["상세 분석 필요"],
            "analysis_date": datetime.now().isoformat(),
            "article_count": len(articles_data),
            "keywords": top_keywords,
            "reasoning": f"기본 분석: {len(articles_data)}개 기사, 평균 센티멘트 {avg_sentiment:.2f}"
        }
    
    def _sentiment_to_numeric(self, sentiment: str) -> float:
        """센티멘트를 숫자로 변환"""
        mapping = {
            'very_negative': -2.0,
            'negative': -1.0,
            'neutral': 0.0,
            'positive': 1.0,
            'very_positive': 2.0
        }
        return mapping.get(sentiment, 0.0)
    
    def _numeric_to_sentiment(self, score: float) -> SentimentScore:
        """숫자를 센티멘트로 변환"""
        if score <= -1.5:
            return SentimentScore.VERY_NEGATIVE
        elif score <= -0.5:
            return SentimentScore.NEGATIVE
        elif score <= 0.5:
            return SentimentScore.NEUTRAL
        elif score <= 1.5:
            return SentimentScore.POSITIVE
        else:
            return SentimentScore.VERY_POSITIVE
    
    def _calculate_basic_impact(self, article_count: int, sentiment_intensity: float) -> ImpactLevel:
        """기본 영향도 계산"""
        import math
        
        volume_score = min(math.log(article_count + 1) / math.log(50), 1.0)
        intensity_score = sentiment_intensity / 2.0
        
        impact_score = (volume_score + intensity_score) / 2
        
        if impact_score >= 0.8:
            return ImpactLevel.VERY_HIGH
        elif impact_score >= 0.6:
            return ImpactLevel.HIGH
        elif impact_score >= 0.4:
            return ImpactLevel.MEDIUM
        elif impact_score >= 0.2:
            return ImpactLevel.LOW
        else:
            return ImpactLevel.VERY_LOW
    
    def _calculate_basic_urgency(self, sentiment_score: float, impact_level: ImpactLevel) -> UrgencyLevel:
        """기본 긴급도 계산"""
        urgency_score = 0.0
        
        # 부정적 센티멘트일수록 긴급도 증가
        if sentiment_score < -1.0:
            urgency_score += 0.4
        elif sentiment_score < 0:
            urgency_score += 0.2
        
        # 영향도가 클수록 긴급도 증가
        impact_multiplier = {
            ImpactLevel.VERY_HIGH: 0.4,
            ImpactLevel.HIGH: 0.3,
            ImpactLevel.MEDIUM: 0.2,
            ImpactLevel.LOW: 0.1,
            ImpactLevel.VERY_LOW: 0.0
        }
        urgency_score += impact_multiplier[impact_level]
        
        # 레벨 결정
        if urgency_score >= 0.7:
            return UrgencyLevel.CRITICAL
        elif urgency_score >= 0.5:
            return UrgencyLevel.HIGH
        elif urgency_score >= 0.3:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW
    
    async def get_stakeholder_comparison(
        self, 
        company_id: int,
        days: int = 30,
        db: Session = None
    ) -> Dict[str, Any]:
        """스테이크홀더 간 비교 분석"""
        
        if db is None:
            db = next(get_db())
            should_close_db = True
        else:
            should_close_db = False
        
        try:
            # 모든 스테이크홀더 인사이트 분석
            insights_result = await self.analyze_stakeholder_insights(
                company_id, None, days, db
            )
            
            if not insights_result.get("success"):
                return insights_result
            
            insights = insights_result["insights"]
            
            # 비교 분석
            comparison = {
                "most_positive": None,
                "most_negative": None,
                "highest_impact": None,
                "most_urgent": None,
                "most_active": None,  # 가장 많은 기사
                "summary": {}
            }
            
            sentiment_scores = {}
            impact_levels = {}
            urgency_levels = {}
            article_counts = {}
            
            for stakeholder_type, insight in insights.items():
                if "error" in insight:
                    continue
                
                sentiment_scores[stakeholder_type] = self._sentiment_to_numeric(insight["sentiment_score"])
                impact_levels[stakeholder_type] = insight["impact_level"]
                urgency_levels[stakeholder_type] = insight["urgency_level"]
                article_counts[stakeholder_type] = insight["article_count"]
            
            # 최고/최저 찾기
            if sentiment_scores:
                comparison["most_positive"] = max(sentiment_scores.items(), key=lambda x: x[1])
                comparison["most_negative"] = min(sentiment_scores.items(), key=lambda x: x[1])
            
            if article_counts:
                comparison["most_active"] = max(article_counts.items(), key=lambda x: x[1])
            
            # 영향도/긴급도는 문자열이므로 별도 처리
            impact_order = ["very_low", "low", "medium", "high", "very_high"]
            urgency_order = ["low", "medium", "high", "critical"]
            
            if impact_levels:
                comparison["highest_impact"] = max(
                    impact_levels.items(), 
                    key=lambda x: impact_order.index(x[1]) if x[1] in impact_order else 0
                )
            
            if urgency_levels:
                comparison["most_urgent"] = max(
                    urgency_levels.items(),
                    key=lambda x: urgency_order.index(x[1]) if x[1] in urgency_order else 0
                )
            
            # 요약 통계
            comparison["summary"] = {
                "total_stakeholders": len(insights),
                "avg_sentiment": sum(sentiment_scores.values()) / len(sentiment_scores) if sentiment_scores else 0,
                "total_articles": sum(article_counts.values()),
                "stakeholders_with_data": len([i for i in insights.values() if "error" not in i and i["article_count"] > 0])
            }
            
            return {
                "success": True,
                "company_id": company_id,
                "comparison": comparison,
                "detailed_insights": insights,
                "analysis_date": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"스테이크홀더 비교 분석 오류: {e}")
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if should_close_db:
                db.close()


# 전역 스테이크홀더 분석 매니저 인스턴스
stakeholder_manager = StakeholderAnalysisManager()


def get_stakeholder_manager() -> StakeholderAnalysisManager:
    """스테이크홀더 분석 매니저 의존성 주입"""
    return stakeholder_manager