"""
고객 스테이크홀더 분석기
"""

from typing import Dict, List
from collections import Counter
import re

from app.stakeholders.base_stakeholder import BaseStakeholderAnalyzer, StakeholderInsight
from database.models import StakeholderType
from app.core.logging import logger


class CustomerAnalyzer(BaseStakeholderAnalyzer):
    """고객 스테이크홀더 분석기"""
    
    def __init__(self):
        super().__init__(StakeholderType.CUSTOMER)
        
        # 고객 특화 가중치 조정
        self.impact_weights = {
            "sentiment_intensity": 0.4,    # 고객 만족도가 가장 중요
            "volume": 0.3,                 # 고객 반응 규모
            "trend": 0.2,                  # 만족도 변화 추이
            "keyword_relevance": 0.1       # 키워드 관련성
        }
    
    def get_specific_keywords(self) -> Dict[str, List[str]]:
        """고객 관련 특화 키워드"""
        return {
            "제품_품질": [
                "품질", "성능", "기능", "디자인", "내구성", "완성도", "퀄리티",
                "작동", "동작", "실행", "구동", "효율", "효과", "결과"
            ],
            "서비스": [
                "서비스", "고객서비스", "AS", "수리", "교환", "환불", "배송",
                "설치", "상담", "응대", "친절", "신속", "정확", "편의"
            ],
            "가격_가치": [
                "가격", "비용", "요금", "할인", "프로모션", "이벤트", "혜택",
                "가성비", "성가비", "경제적", "저렴", "비싸다", "합리적"
            ],
            "사용_경험": [
                "사용", "이용", "경험", "체험", "느낌", "인상", "만족", "불만",
                "편리", "불편", "쉽다", "어렵다", "직관적", "복잡"
            ],
            "구매_과정": [
                "구매", "주문", "결제", "배송", "포장", "개봉", "설치", "설정",
                "등록", "인증", "활성화", "시작", "첫인상"
            ],
            "문제_이슈": [
                "문제", "이슈", "오류", "에러", "버그", "결함", "불량", "고장",
                "작동안함", "먹통", "느림", "지연", "중단", "실패"
            ],
            "추천_재구매": [
                "추천", "권장", "소개", "재구매", "재이용", "다시", "또", "계속",
                "지속", "유지", "연장", "갱신", "업그레이드"
            ]
        }
    
    def analyze_concerns(self, articles_data: List[Dict]) -> List[str]:
        """고객 주요 관심사 분석"""
        concerns = []
        keywords = self.get_specific_keywords()
        
        # 부정적 기사에서 주요 이슈 추출
        negative_articles = [
            article for article in articles_data 
            if article.get('sentiment_score') in ['negative', 'very_negative']
        ]
        
        if negative_articles:
            concern_counts = Counter()
            
            for article in negative_articles:
                content = f"{article.get('title', '')} {article.get('content', '')}".lower()
                
                for category, words in keywords.items():
                    if any(word in content for word in words):
                        concern_counts[category] += 1
            
            # 상위 관심사 추출
            top_concerns = concern_counts.most_common(5)
            concerns = [self._translate_concern(concern) for concern, count in top_concerns]
        
        # 전체 기사에서 자주 언급되는 주제도 포함
        all_content = " ".join([
            f"{article.get('title', '')} {article.get('content', '')}" 
            for article in articles_data
        ]).lower()
        
        # 특정 패턴 검색
        if "배송" in all_content or "택배" in all_content:
            concerns.append("배송 서비스")
        if "가격" in all_content or "비용" in all_content:
            concerns.append("가격 정책")
        if "품질" in all_content or "성능" in all_content:
            concerns.append("제품 품질")
        
        return list(set(concerns))[:5]  # 중복 제거 후 상위 5개
    
    def generate_action_items(self, insight: StakeholderInsight) -> List[str]:
        """고객 대상 권장 액션 아이템 생성"""
        actions = []
        
        # 센티멘트 기반 액션
        if insight.sentiment_score.value in ['negative', 'very_negative']:
            actions.extend([
                "고객 불만 사항 즉시 파악 및 대응",
                "고객 서비스팀 강화 및 교육 실시",
                "제품/서비스 개선 계획 수립"
            ])
        elif insight.sentiment_score.value in ['positive', 'very_positive']:
            actions.extend([
                "긍정적 고객 후기 마케팅 활용",
                "만족 고객 대상 추가 상품 제안",
                "고객 추천 프로그램 강화"
            ])
        
        # 영향도 기반 액션
        if insight.impact_level.value in ['high', 'very_high']:
            actions.append("고객 센티멘트 실시간 모니터링 강화")
            
        # 긴급도 기반 액션
        if insight.urgency_level.value in ['high', 'critical']:
            actions.extend([
                "긴급 고객 대응팀 가동",
                "경영진 보고 및 즉시 대응 방안 수립"
            ])
        
        # 관심사 기반 액션
        for concern in insight.key_concerns:
            if "품질" in concern:
                actions.append("제품 품질 관리 시스템 점검")
            elif "서비스" in concern:
                actions.append("고객 서비스 프로세스 개선")
            elif "가격" in concern:
                actions.append("가격 정책 재검토 및 경쟁력 분석")
            elif "배송" in concern:
                actions.append("배송 서비스 파트너사 점검")
        
        # 부정 요인 기반 액션
        for factor in insight.negative_factors:
            if "문제_이슈" in factor:
                actions.append("기술 지원팀 대응 역량 강화")
            elif "사용_경험" in factor:
                actions.append("사용자 경험(UX) 개선 프로젝트 시작")
        
        return list(set(actions))[:7]  # 중복 제거 후 상위 7개
    
    def get_description(self) -> str:
        """고객 스테이크홀더 설명"""
        return "제품이나 서비스를 구매하고 사용하는 최종 소비자 그룹으로, 기업의 매출과 브랜드 이미지에 직접적인 영향을 미치는 핵심 스테이크홀더입니다."
    
    def get_key_metrics(self) -> List[str]:
        """고객 관련 주요 지표"""
        return [
            "고객 만족도 (CSAT)",
            "순추천지수 (NPS)", 
            "고객 이탈률",
            "재구매율",
            "고객 생애 가치 (CLV)",
            "고객 서비스 응답 시간",
            "제품 품질 점수",
            "가격 만족도"
        ]
    
    def _translate_concern(self, concern_key: str) -> str:
        """관심사 키를 한국어로 번역"""
        translations = {
            "제품_품질": "제품 품질",
            "서비스": "고객 서비스",
            "가격_가치": "가격 및 가치",
            "사용_경험": "사용자 경험",
            "구매_과정": "구매 프로세스",
            "문제_이슈": "제품/서비스 문제",
            "추천_재구매": "재구매 및 추천"
        }
        return translations.get(concern_key, concern_key)