"""
센티멘트 분석 기본 클래스
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import numpy as np

from app.core.logging import logger
from database.models import SentimentScore, StakeholderType


class AnalysisConfidence(Enum):
    """분석 신뢰도 레벨"""
    VERY_LOW = "very_low"      # 0.0 - 0.3
    LOW = "low"                # 0.3 - 0.5
    MEDIUM = "medium"          # 0.5 - 0.7
    HIGH = "high"              # 0.7 - 0.9
    VERY_HIGH = "very_high"    # 0.9 - 1.0


@dataclass
class SentimentResult:
    """센티멘트 분석 결과"""
    sentiment_score: SentimentScore
    confidence: float
    confidence_level: AnalysisConfidence
    probabilities: Dict[str, float]  # 각 감정별 확률
    keywords: List[str]
    reasoning: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "sentiment_score": self.sentiment_score.value,
            "confidence": self.confidence,
            "confidence_level": self.confidence_level.value,
            "probabilities": self.probabilities,
            "keywords": self.keywords,
            "reasoning": self.reasoning
        }


@dataclass
class StakeholderResult:
    """스테이크홀더 분류 결과"""
    stakeholder_type: StakeholderType
    confidence: float
    probabilities: Dict[str, float]  # 각 스테이크홀더별 확률
    reasoning: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "stakeholder_type": self.stakeholder_type.value,
            "confidence": self.confidence,
            "probabilities": self.probabilities,
            "reasoning": self.reasoning
        }


@dataclass
class AnalysisInput:
    """분석 입력 데이터"""
    title: str
    content: str
    company_name: str
    author: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    
    def get_full_text(self) -> str:
        """전체 텍스트 반환"""
        return f"{self.title} {self.content}".strip()


class BaseSentimentAnalyzer(ABC):
    """센티멘트 분석기 기본 클래스"""
    
    def __init__(self, model_name: str = "base"):
        self.model_name = model_name
        self.is_loaded = False
        self.confidence_threshold = 0.7
        
        # 감정 점수 매핑
        self.sentiment_mapping = {
            SentimentScore.VERY_NEGATIVE: -2,
            SentimentScore.NEGATIVE: -1,
            SentimentScore.NEUTRAL: 0,
            SentimentScore.POSITIVE: 1,
            SentimentScore.VERY_POSITIVE: 2
        }
        
        # 신뢰도 레벨 매핑
        self.confidence_levels = {
            (0.0, 0.3): AnalysisConfidence.VERY_LOW,
            (0.3, 0.5): AnalysisConfidence.LOW,
            (0.5, 0.7): AnalysisConfidence.MEDIUM,
            (0.7, 0.9): AnalysisConfidence.HIGH,
            (0.9, 1.0): AnalysisConfidence.VERY_HIGH
        }
    
    @abstractmethod
    async def load_model(self) -> bool:
        """모델 로드"""
        pass
    
    @abstractmethod
    async def analyze_sentiment(self, text_input: AnalysisInput) -> SentimentResult:
        """센티멘트 분석"""
        pass
    
    @abstractmethod
    async def classify_stakeholder(self, text_input: AnalysisInput) -> StakeholderResult:
        """스테이크홀더 분류"""
        pass
    
    def get_confidence_level(self, confidence: float) -> AnalysisConfidence:
        """신뢰도 점수를 레벨로 변환"""
        for (min_val, max_val), level in self.confidence_levels.items():
            if min_val <= confidence < max_val:
                return level
        return AnalysisConfidence.VERY_HIGH if confidence >= 0.9 else AnalysisConfidence.VERY_LOW
    
    def score_to_sentiment(self, score: float) -> SentimentScore:
        """점수를 센티멘트로 변환"""
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
    
    def preprocess_text(self, text: str) -> str:
        """텍스트 전처리"""
        if not text:
            return ""
        
        # 기본 정제
        import re
        
        # HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # 특수 문자 정제
        text = re.sub(r'&nbsp;|&amp;|&lt;|&gt;|&quot;|&#\d+;', ' ', text)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """키워드 추출 (기본 구현)"""
        if not text:
            return []
        
        import re
        from collections import Counter
        
        # 한글, 영문 단어 추출
        words = re.findall(r'[가-힣]{2,}|[a-zA-Z]{3,}', text.lower())
        
        # 불용어 제거 (기본적인 것들만)
        stopwords = {
            '그리고', '하지만', '그러나', '또한', '따라서', '그래서', '이것', '그것', '저것',
            '이런', '그런', '저런', '이렇게', '그렇게', '저렇게', '여기서', '거기서', '저기서',
            'and', 'but', 'or', 'so', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during'
        }
        
        # 불용어가 아닌 단어들만 필터링
        filtered_words = [word for word in words if word not in stopwords and len(word) > 1]
        
        # 빈도 계산 및 상위 키워드 반환
        word_counts = Counter(filtered_words)
        keywords = [word for word, count in word_counts.most_common(max_keywords)]
        
        return keywords
    
    def validate_input(self, text_input: AnalysisInput) -> bool:
        """입력 데이터 유효성 검증"""
        if not text_input.title and not text_input.content:
            logger.warning("제목과 내용이 모두 비어있습니다")
            return False
        
        full_text = text_input.get_full_text()
        if len(full_text.strip()) < 10:
            logger.warning("텍스트가 너무 짧습니다")
            return False
        
        return True
    
    async def batch_analyze(
        self, 
        inputs: List[AnalysisInput], 
        batch_size: int = 32
    ) -> List[Tuple[SentimentResult, StakeholderResult]]:
        """배치 분석"""
        results = []
        
        for i in range(0, len(inputs), batch_size):
            batch = inputs[i:i + batch_size]
            batch_results = []
            
            for text_input in batch:
                try:
                    if not self.validate_input(text_input):
                        # 기본값 반환
                        sentiment_result = SentimentResult(
                            sentiment_score=SentimentScore.NEUTRAL,
                            confidence=0.0,
                            confidence_level=AnalysisConfidence.VERY_LOW,
                            probabilities={},
                            keywords=[],
                            reasoning="입력 데이터 유효성 검증 실패"
                        )
                        stakeholder_result = StakeholderResult(
                            stakeholder_type=StakeholderType.MEDIA,
                            confidence=0.0,
                            probabilities={},
                            reasoning="입력 데이터 유효성 검증 실패"
                        )
                        batch_results.append((sentiment_result, stakeholder_result))
                        continue
                    
                    # 센티멘트 분석
                    sentiment_result = await self.analyze_sentiment(text_input)
                    
                    # 스테이크홀더 분류
                    stakeholder_result = await self.classify_stakeholder(text_input)
                    
                    batch_results.append((sentiment_result, stakeholder_result))
                    
                except Exception as e:
                    logger.error(f"분석 오류: {e}")
                    # 에러 시 기본값 반환
                    sentiment_result = SentimentResult(
                        sentiment_score=SentimentScore.NEUTRAL,
                        confidence=0.0,
                        confidence_level=AnalysisConfidence.VERY_LOW,
                        probabilities={},
                        keywords=[],
                        reasoning=f"분석 오류: {str(e)}"
                    )
                    stakeholder_result = StakeholderResult(
                        stakeholder_type=StakeholderType.MEDIA,
                        confidence=0.0,
                        probabilities={},
                        reasoning=f"분석 오류: {str(e)}"
                    )
                    batch_results.append((sentiment_result, stakeholder_result))
            
            results.extend(batch_results)
            
            # 배치 간 잠시 대기 (메모리 관리)
            if i + batch_size < len(inputs):
                import asyncio
                await asyncio.sleep(0.1)
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            "model_name": self.model_name,
            "is_loaded": self.is_loaded,
            "confidence_threshold": self.confidence_threshold,
            "supported_languages": ["ko", "en"],
            "model_type": self.__class__.__name__
        }