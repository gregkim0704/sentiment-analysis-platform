"""
투자자 스테이크홀더 분석기
"""

from typing import Dict, List
from collections import Counter
import re

from app.stakeholders.base_stakeholder import BaseStakeholderAnalyzer, StakeholderInsight
from database.models import StakeholderType
from app.core.logging import logger


class InvestorAnalyzer(BaseStakeholderAnalyzer):
    """투자자 스테이크홀더 분석기"""
    
    def __init__(self):
        super().__init__(StakeholderType.INVESTOR)
        
        # 투자자 특화 가중치 조정
        self.impact_weights = {
            "sentiment_intensity": 0.35,   # 투자 심리 중요
            "volume": 0.25,                # 시장 관심도
            "trend": 0.35,                 # 트렌드 변화가 매우 중요
            "keyword_relevance": 0.05      # 키워드는 상대적으로 덜 중요
        }
    
    def get_specific_keywords(self) -> Dict[str, List[str]]:
        """투자자 관련 특화 키워드"""
        return {
            "재무_실적": [
                "매출", "영업이익", "순이익", "실적", "수익", "손익", "EBITDA",
                "ROE", "ROA", "부채비율", "유동비율", "자기자본", "총자산"
            ],
            "주가_주식": [
                "주가", "주식", "시가총액", "거래량", "상승", "하락", "등락",
                "목표주가", "적정주가", "저평가", "고평가", "PER", "PBR"
            ],
            "배당_수익": [
                "배당", "배당금", "배당률", "배당수익률", "주주환원", "자사주매입",
                "무상증자", "유상증자", "감자", "분할", "합병"
            ],
            "성장_전망": [
                "성장", "성장률", "전망", "예상", "예측", "목표", "계획", "전략",
                "비전", "로드맵", "확장", "진출", "투자", "개발"
            ],
            "리스크_위험": [
                "리스크", "위험", "불확실성", "변동성", "하방", "손실", "적자",
                "부진", "악화", "우려", "경고", "주의", "위기"
            ],
            "시장_경쟁": [
                "시장", "시장점유율", "경쟁", "경쟁력", "경쟁사", "업계", "산업",
                "트렌드", "수요", "공급", "가격", "마진"
            ],
            "거버넌스": [
                "지배구조", "이사회", "감사", "투명성", "공시", "IR", "주주총회",
                "의결권", "경영진", "CEO", "CFO", "교체", "선임"
            ],
            "ESG": [
                "ESG", "환경", "사회", "지배구조", "지속가능", "친환경", "탄소중립",
                "사회적책임", "윤리", "컴플라이언스", "규제", "준수"
            ]
        }
    
    def analyze_concerns(self, articles_data: List[Dict]) -> List[str]:
        """투자자 주요 관심사 분석"""
        concerns = []
        keywords = self.get_specific_keywords()
        
        # 모든 기사에서 관심사 추출 (투자자는 긍정/부정 모두 중요)
        concern_counts = Counter()
        
        for article in articles_data:
            content = f"{article.get('title', '')} {article.get('content', '')}".lower()
            
            for category, words in keywords.items():
                if any(word in content for word in words):
                    # 부정적 기사는 가중치 2배
                    weight = 2 if article.get('sentiment_score') in ['negative', 'very_negative'] else 1
                    concern_counts[category] += weight
        
        # 상위 관심사 추출
        top_concerns = concern_counts.most_common(5)
        concerns = [self._translate_concern(concern) for concern, count in top_concerns]
        
        # 특정 패턴 기반 관심사 추가
        all_content = " ".join([
            f"{article.get('title', '')} {article.get('content', '')}" 
            for article in articles_data
        ]).lower()
        
        # 실적 관련
        if any(word in all_content for word in ["실적", "매출", "영업이익", "순이익"]):
            if "실적 발표" not in concerns:
                concerns.append("실적 발표")
        
        # 주가 관련
        if any(word in all_content for word in ["주가", "목표주가", "상승", "하락"]):
            if "주가 동향" not in concerns:
                concerns.append("주가 동향")
        
        # 배당 관련
        if any(word in all_content for word in ["배당", "배당금", "주주환원"]):
            if "배당 정책" not in concerns:
                concerns.append("배당 정책")
        
        return concerns[:5]
    
    def generate_action_items(self, insight: StakeholderInsight) -> List[str]:
        """투자자 대상 권장 액션 아이템 생성"""
        actions = []
        
        # 센티멘트 기반 액션
        if insight.sentiment_score.value in ['negative', 'very_negative']:
            actions.extend([
                "투자자 대상 긴급 IR 설명회 개최",
                "부정적 이슈에 대한 명확한 해명 자료 배포",
                "경영진 투자자 미팅 일정 확대",
                "애널리스트 대상 컨퍼런스콜 실시"
            ])
        elif insight.sentiment_score.value in ['positive', 'very_positive']:
            actions.extend([
                "긍정적 모멘텀 활용한 IR 로드쇼 기획",
                "기관투자자 대상 추가 미팅 추진",
                "성과 홍보를 위한 미디어 인터뷰 확대"
            ])
        
        # 영향도 기반 액션
        if insight.impact_level.value in ['high', 'very_high']:
            actions.extend([
                "주가 및 거래량 실시간 모니터링 강화",
                "투자자 센티멘트 일일 리포트 작성"
            ])
            
        # 긴급도 기반 액션
        if insight.urgency_level.value in ['high', 'critical']:
            actions.extend([
                "경영진 긴급 대응팀 구성",
                "주요 기관투자자 개별 연락",
                "공시 및 보도자료 즉시 검토"
            ])
        
        # 관심사 기반 액션
        for concern in insight.key_concerns:
            if "실적" in concern:
                actions.append("실적 가이던스 업데이트 및 소통 강화")
            elif "주가" in concern:
                actions.append("주가 변동 요인 분석 및 대응 방안 수립")
            elif "배당" in concern:
                actions.append("주주환원 정책 재검토 및 커뮤니케이션")
            elif "ESG" in concern:
                actions.append("ESG 경영 성과 및 계획 적극 홍보")
            elif "거버넌스" in concern:
                actions.append("지배구조 개선 방안 검토 및 공시")
        
        # 부정 요인 기반 액션
        for factor in insight.negative_factors:
            if "리스크_위험" in factor:
                actions.append("리스크 관리 체계 점검 및 보완")
            elif "재무_실적" in factor:
                actions.append("재무 구조 개선 계획 수립")
        
        return list(set(actions))[:8]  # 중복 제거 후 상위 8개
    
    def get_description(self) -> str:
        """투자자 스테이크홀더 설명"""
        return "기업의 주식을 보유하거나 투자를 고려하는 개인 및 기관투자자로, 기업의 재무성과와 성장전망에 높은 관심을 가지며 주가에 직접적인 영향을 미치는 핵심 스테이크홀더입니다."
    
    def get_key_metrics(self) -> List[str]:
        """투자자 관련 주요 지표"""
        return [
            "주가 수익률",
            "주가 변동성",
            "거래량",
            "기관투자자 지분율",
            "애널리스트 목표주가",
            "PER (주가수익비율)",
            "PBR (주가순자산비율)",
            "배당수익률",
            "ROE (자기자본수익률)",
            "부채비율"
        ]
    
    def _translate_concern(self, concern_key: str) -> str:
        """관심사 키를 한국어로 번역"""
        translations = {
            "재무_실적": "재무 실적",
            "주가_주식": "주가 동향",
            "배당_수익": "배당 정책",
            "성장_전망": "성장 전망",
            "리스크_위험": "투자 리스크",
            "시장_경쟁": "시장 경쟁력",
            "거버넌스": "기업 지배구조",
            "ESG": "ESG 경영"
        }
        return translations.get(concern_key, concern_key)