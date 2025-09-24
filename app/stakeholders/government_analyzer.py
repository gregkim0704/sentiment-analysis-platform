"""
정부/규제기관 스테이크홀더 분석기
"""

from typing import Dict, List
from collections import Counter

from app.stakeholders.base_stakeholder import BaseStakeholderAnalyzer, StakeholderInsight
from database.models import StakeholderType


class GovernmentAnalyzer(BaseStakeholderAnalyzer):
    """정부/규제기관 스테이크홀더 분석기"""
    
    def __init__(self):
        super().__init__(StakeholderType.GOVERNMENT)
        
        # 정부 특화 가중치 조정
        self.impact_weights = {
            "sentiment_intensity": 0.3,    # 정부 반응
            "volume": 0.2,                 # 언급량
            "trend": 0.4,                  # 정책 변화 추이가 중요
            "keyword_relevance": 0.1       # 키워드 관련성
        }
    
    def get_specific_keywords(self) -> Dict[str, List[str]]:
        """정부/규제기관 관련 특화 키워드"""
        return {
            "규제_법률": ["규제", "법률", "법안", "제도", "정책", "가이드라인", "기준", "표준"],
            "허가_승인": ["허가", "승인", "인증", "등록", "신고", "면허", "자격"],
            "감독_점검": ["감독", "점검", "조사", "감사", "검사", "모니터링"],
            "제재_처벌": ["제재", "처벌", "과태료", "벌금", "영업정지", "취소"],
            "세금_지원": ["세금", "세제", "지원금", "보조금", "혜택", "인센티브"],
            "공공정책": ["공공", "국가", "정부", "부처", "청", "위원회"]
        }
    
    def analyze_concerns(self, articles_data: List[Dict]) -> List[str]:
        """정부 관련 주요 관심사 분석"""
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
        """정부 대상 권장 액션 아이템 생성"""
        actions = []
        
        if insight.sentiment_score.value in ['negative', 'very_negative']:
            actions.extend([
                "정부 관계자와 긴급 미팅 요청",
                "규제 대응 전담팀 가동",
                "법무팀 컴플라이언스 점검"
            ])
        
        if insight.urgency_level.value in ['high', 'critical']:
            actions.append("정부 정책 변화 모니터링 강화")
        
        return actions[:5]
    
    def get_description(self) -> str:
        return "기업 활동을 규제하고 감독하는 정부기관 및 규제당국으로, 정책 변화와 규제 준수가 기업 운영에 중대한 영향을 미칩니다."
    
    def get_key_metrics(self) -> List[str]:
        return ["규제 준수율", "정부 정책 변화", "허가/승인 현황", "제재 이력"]
    
    def _translate_concern(self, concern_key: str) -> str:
        translations = {
            "규제_법률": "규제 및 법률",
            "허가_승인": "허가 및 승인",
            "감독_점검": "감독 및 점검",
            "제재_처벌": "제재 및 처벌",
            "세금_지원": "세제 및 지원",
            "공공정책": "공공정책"
        }
        return translations.get(concern_key, concern_key)