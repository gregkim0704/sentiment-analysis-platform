"""
스테이크홀더 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import re
from datetime import datetime, timedelta

from app.core.logging import logger
from database.models import StakeholderType, SentimentScore


class ImpactLevel(Enum):
    """영향도 레벨"""
    VERY_LOW = "very_low"      # 0.0 - 0.2
    LOW = "low"                # 0.2 - 0.4
    MEDIUM = "medium"          # 0.4 - 0.6
    HIGH = "high"              # 0.6 - 0.8
    VERY_HIGH = "very_high"    # 0.8 - 1.0


class UrgencyLevel(Enum):
    """긴급도 레벨"""
    LOW = "low"                # 일반적인 모니터링
    MEDIUM = "medium"          # 주의 깊은 관찰
    HIGH = "high"              # 즉시 대응 필요
    CRITICAL = "critical"      # 긴급 대응 필요


@dataclass
class StakeholderInsight:
    """스테이크홀더 인사이트"""
    stakeholder_type: StakeholderType
    sentiment_score: SentimentScore
    confidence: float
    impact_level: ImpactLevel
    urgency_level: UrgencyLevel
    
    # 상세 분석 결과
    key_concerns: List[str]           # 주요 관심사
    positive_factors: List[str]       # 긍정 요인
    negative_factors: List[str]       # 부정 요인
    action_items: List[str]           # 권장 액션
    
    # 메타데이터
    analysis_date: datetime
    article_count: int
    keywords: List[str]
    reasoning: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "stakeholder_type": self.stakeholder_type.value,
            "sentiment_score": self.sentiment_score.value,
            "confidence": self.confidence,
            "impact_level": self.impact_level.value,
            "urgency_level": self.urgency_level.value,
            "key_concerns": self.key_concerns,
            "positive_factors": self.positive_factors,
            "negative_factors": self.negative_factors,
            "action_items": self.action_items,
            "analysis_date": self.analysis_date.isoformat(),
            "article_count": self.article_count,
            "keywords": self.keywords,
            "reasoning": self.reasoning
        }


@dataclass
class StakeholderTrend:
    """스테이크홀더 트렌드"""
    stakeholder_type: StakeholderType
    period_days: int
    
    # 트렌드 데이터
    sentiment_trend: List[Tuple[datetime, float]]  # (날짜, 센티멘트 점수)
    volume_trend: List[Tuple[datetime, int]]       # (날짜, 기사 수)
    
    # 변화율
    sentiment_change: float                        # 센티멘트 변화율 (%)
    volume_change: float                          # 볼륨 변화율 (%)
    
    # 통계
    avg_sentiment: float
    sentiment_volatility: float
    peak_dates: List[datetime]                    # 주요 이벤트 날짜
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "stakeholder_type": self.stakeholder_type.value,
            "period_days": self.period_days,
            "sentiment_trend": [(date.isoformat(), score) for date, score in self.sentiment_trend],
            "volume_trend": [(date.isoformat(), count) for date, count in self.volume_trend],
            "sentiment_change": self.sentiment_change,
            "volume_change": self.volume_change,
            "avg_sentiment": self.avg_sentiment,
            "sentiment_volatility": self.sentiment_volatility,
            "peak_dates": [date.isoformat() for date in self.peak_dates]
        }


class BaseStakeholderAnalyzer(ABC):
    """스테이크홀더 분석기 기본 클래스"""
    
    def __init__(self, stakeholder_type: StakeholderType):
        self.stakeholder_type = stakeholder_type
        self.name = stakeholder_type.value
        
        # 영향도 가중치 (스테이크홀더별로 다름)
        self.impact_weights = {
            "sentiment_intensity": 0.3,    # 센티멘트 강도
            "volume": 0.2,                 # 언급량
            "trend": 0.2,                  # 트렌드 변화
            "keyword_relevance": 0.3       # 키워드 관련성
        }
        
        # 긴급도 임계값
        self.urgency_thresholds = {
            UrgencyLevel.CRITICAL: 0.9,
            UrgencyLevel.HIGH: 0.7,
            UrgencyLevel.MEDIUM: 0.5,
            UrgencyLevel.LOW: 0.0
        }
    
    @abstractmethod
    def get_specific_keywords(self) -> Dict[str, List[str]]:
        """스테이크홀더별 특화 키워드 반환"""
        pass
    
    @abstractmethod
    def analyze_concerns(self, articles_data: List[Dict]) -> List[str]:
        """주요 관심사 분석"""
        pass
    
    @abstractmethod
    def generate_action_items(self, insight: StakeholderInsight) -> List[str]:
        """권장 액션 아이템 생성"""
        pass
    
    def calculate_impact_level(self, 
                             sentiment_score: float, 
                             article_count: int, 
                             trend_change: float,
                             keyword_relevance: float) -> ImpactLevel:
        """영향도 레벨 계산"""
        
        # 센티멘트 강도 (절댓값)
        sentiment_intensity = abs(sentiment_score) / 2.0  # -2~2를 0~1로 정규화
        
        # 볼륨 점수 (로그 스케일)
        import math
        volume_score = min(math.log(article_count + 1) / math.log(100), 1.0)
        
        # 트렌드 변화 점수 (절댓값)
        trend_score = min(abs(trend_change) / 100.0, 1.0)
        
        # 가중 평균 계산
        impact_score = (
            sentiment_intensity * self.impact_weights["sentiment_intensity"] +
            volume_score * self.impact_weights["volume"] +
            trend_score * self.impact_weights["trend"] +
            keyword_relevance * self.impact_weights["keyword_relevance"]
        )
        
        # 레벨 결정
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
    
    def calculate_urgency_level(self, 
                              sentiment_score: float, 
                              impact_level: ImpactLevel,
                              trend_change: float) -> UrgencyLevel:
        """긴급도 레벨 계산"""
        
        # 기본 긴급도 점수
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
        
        # 급격한 변화일수록 긴급도 증가
        if abs(trend_change) > 50:
            urgency_score += 0.3
        elif abs(trend_change) > 20:
            urgency_score += 0.2
        
        # 레벨 결정
        for level, threshold in sorted(self.urgency_thresholds.items(), 
                                     key=lambda x: x[1], reverse=True):
            if urgency_score >= threshold:
                return level
        
        return UrgencyLevel.LOW
    
    def extract_factors(self, articles_data: List[Dict]) -> Tuple[List[str], List[str]]:
        """긍정/부정 요인 추출"""
        positive_factors = []
        negative_factors = []
        
        # 스테이크홀더별 특화 키워드
        keywords = self.get_specific_keywords()
        
        for article in articles_data:
            content = f"{article.get('title', '')} {article.get('content', '')}".lower()
            sentiment = article.get('sentiment_score')
            
            # 긍정적 기사에서 긍정 요인 추출
            if sentiment in ['positive', 'very_positive']:
                for category, words in keywords.items():
                    for word in words:
                        if word in content and category not in positive_factors:
                            positive_factors.append(category)
                            break
            
            # 부정적 기사에서 부정 요인 추출
            elif sentiment in ['negative', 'very_negative']:
                for category, words in keywords.items():
                    for word in words:
                        if word in content and category not in negative_factors:
                            negative_factors.append(category)
                            break
        
        return positive_factors[:5], negative_factors[:5]  # 상위 5개씩
    
    def calculate_keyword_relevance(self, articles_data: List[Dict]) -> float:
        """키워드 관련성 점수 계산"""
        if not articles_data:
            return 0.0
        
        keywords = self.get_specific_keywords()
        total_relevance = 0.0
        
        for article in articles_data:
            content = f"{article.get('title', '')} {article.get('content', '')}".lower()
            article_relevance = 0.0
            
            for category, words in keywords.items():
                category_matches = sum(1 for word in words if word in content)
                if category_matches > 0:
                    article_relevance += min(category_matches / len(words), 1.0)
            
            total_relevance += article_relevance / len(keywords)
        
        return min(total_relevance / len(articles_data), 1.0)
    
    def analyze_stakeholder_insight(self, 
                                  articles_data: List[Dict],
                                  trend_data: Optional[Dict] = None) -> StakeholderInsight:
        """스테이크홀더 인사이트 분석"""
        
        if not articles_data:
            return self._create_empty_insight()
        
        # 기본 통계 계산
        sentiments = [self._sentiment_to_numeric(article.get('sentiment_score', 'neutral')) 
                     for article in articles_data]
        avg_sentiment = sum(sentiments) / len(sentiments)
        confidence = sum(article.get('sentiment_confidence', 0.0) for article in articles_data) / len(articles_data)
        
        # 센티멘트 점수를 enum으로 변환
        sentiment_enum = self._numeric_to_sentiment(avg_sentiment)
        
        # 트렌드 변화율 계산
        trend_change = trend_data.get('sentiment_change', 0.0) if trend_data else 0.0
        
        # 키워드 관련성 계산
        keyword_relevance = self.calculate_keyword_relevance(articles_data)
        
        # 영향도 및 긴급도 계산
        impact_level = self.calculate_impact_level(
            avg_sentiment, len(articles_data), trend_change, keyword_relevance
        )
        urgency_level = self.calculate_urgency_level(
            avg_sentiment, impact_level, trend_change
        )
        
        # 주요 관심사 분석
        key_concerns = self.analyze_concerns(articles_data)
        
        # 긍정/부정 요인 추출
        positive_factors, negative_factors = self.extract_factors(articles_data)
        
        # 키워드 추출
        all_keywords = []
        for article in articles_data:
            if article.get('keywords'):
                all_keywords.extend(article['keywords'])
        
        from collections import Counter
        top_keywords = [word for word, count in Counter(all_keywords).most_common(10)]
        
        # 인사이트 생성
        insight = StakeholderInsight(
            stakeholder_type=self.stakeholder_type,
            sentiment_score=sentiment_enum,
            confidence=confidence,
            impact_level=impact_level,
            urgency_level=urgency_level,
            key_concerns=key_concerns,
            positive_factors=positive_factors,
            negative_factors=negative_factors,
            action_items=[],  # 나중에 생성
            analysis_date=datetime.now(),
            article_count=len(articles_data),
            keywords=top_keywords,
            reasoning=f"{self.name} 그룹 분석: {len(articles_data)}개 기사, 평균 센티멘트 {avg_sentiment:.2f}"
        )
        
        # 액션 아이템 생성
        insight.action_items = self.generate_action_items(insight)
        
        return insight
    
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
    
    def _create_empty_insight(self) -> StakeholderInsight:
        """빈 인사이트 생성"""
        return StakeholderInsight(
            stakeholder_type=self.stakeholder_type,
            sentiment_score=SentimentScore.NEUTRAL,
            confidence=0.0,
            impact_level=ImpactLevel.VERY_LOW,
            urgency_level=UrgencyLevel.LOW,
            key_concerns=[],
            positive_factors=[],
            negative_factors=[],
            action_items=["데이터 부족으로 분석 불가"],
            analysis_date=datetime.now(),
            article_count=0,
            keywords=[],
            reasoning="분석할 데이터가 없습니다"
        )
    
    def get_stakeholder_info(self) -> Dict[str, Any]:
        """스테이크홀더 정보 반환"""
        return {
            "type": self.stakeholder_type.value,
            "name": self.name,
            "description": self.get_description(),
            "key_metrics": self.get_key_metrics(),
            "impact_weights": self.impact_weights
        }
    
    @abstractmethod
    def get_description(self) -> str:
        """스테이크홀더 설명 반환"""
        pass
    
    @abstractmethod
    def get_key_metrics(self) -> List[str]:
        """주요 지표 목록 반환"""
        pass