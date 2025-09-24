"""
언론 스테이크홀더 분석기
"""

from typing import Dict, List
from collections import Counter

from app.stakeholders.base_stakeholder import BaseStakeholderAnalyzer, StakeholderInsight
from database.models import StakeholderType


class MediaAnalyzer(BaseStakeholderAnalyzer):
    """언론 스테이크홀더 분석기"""
    
    def __init__(self):
        super().__init__(StakeholderType.MEDIA)
        
        # 언론 특화 가중치 조정
        self.impact_weights = {
            "sentiment_intensity": 0.25,   # 언론 톤
            "volume": 0.4,                 # 보도량이 가장 중요
            "trend": 0.25,                 # 보도 트렌드
            "keyword_relevance": 0.1       # 키워드 관련성
        }
    
    def get_specific_keywords(self) -> Dict[str, List[str]]:
        """언론 관련 특화 키워드"""
        return {
            "보도_취재": ["보도", "취재", "기사", "뉴스", "리포트", "특집", "인터뷰"],
            "발표_공시": ["발표", "공시", "보도자료", "브리핑", "컨퍼런스"],
            "이슈_사건": ["이슈", "사건", "논란", "화제", "관심", "주목"],
            "평가_분석": ["평가", "분석", "전망", "예측", "의견", "시각"],
            "홍보_마케팅": ["홍보", "마케팅", "광고", "캠페인", "이벤트"],
            "위기_스캔들": ["위기", "스캔들", "문제", "비판", "지적", "우려"]
        }
    
    def analyze_concerns(self, articles_data: List[Dict]) -> List[str]:
        """언론 관련 주요 관심사 분석"""
        concerns = []
        keywords = self.get_specific_keywords()
        
        concern_counts = Counter()
        for article in articles_data:
            content = f"{article.get('title', '')} {article.get('content', '')}".lower()
            for category, words in keywords.items():
                if any(word in content for word in words):
                    concern_counts[category] += 1
        
        top_concerns = concern_counts.most_common(3)
        concerns = [self._translate_concern(concern) for concern, count in top_concerns]
        
        return concerns
    
    def generate_action_items(self, insight: StakeholderInsight) -> List[str]:
        """언론 대상 권장 액션 아이템 생성"""
        actions = []
        
        if insight.sentiment_score.value in ['negative', 'very_negative']:
            actions.extend([
                "언론 대응 전략 수립",
                "PR팀 위기 대응 모드 전환",
                "기자 간담회 개최 검토"
            ])
        elif insight.sentiment_score.value in ['positive', 'very_positive']:
            actions.extend([
                "긍정적 보도 확산 전략 수립",
                "추가 미디어 노출 기회 모색"
            ])
        
        if insight.impact_level.value in ['high', 'very_high']:
            actions.append("언론 모니터링 강화")
        
        return actions[:5]
    
    def get_description(self) -> str:
        return "기업의 활동과 성과를 보도하고 평가하는 언론기관으로, 대중 인식과 브랜드 이미지 형성에 결정적인 영향을 미칩니다."
    
    def get_key_metrics(self) -> List[str]:
        return ["보도량", "긍정 보도 비율", "언론사별 톤", "이슈 확산도"]
    
    def _translate_concern(self, concern_key: str) -> str:
        translations = {
            "보도_취재": "보도 및 취재",
            "발표_공시": "발표 및 공시",
            "이슈_사건": "이슈 및 사건",
            "평가_분석": "평가 및 분석",
            "홍보_마케팅": "홍보 및 마케팅",
            "위기_스캔들": "위기 및 스캔들"
        }
        return translations.get(concern_key, concern_key)