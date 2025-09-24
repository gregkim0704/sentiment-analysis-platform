"""
직원 스테이크홀더 분석기
"""

from typing import Dict, List
from collections import Counter
import re

from app.stakeholders.base_stakeholder import BaseStakeholderAnalyzer, StakeholderInsight
from database.models import StakeholderType
from app.core.logging import logger


class EmployeeAnalyzer(BaseStakeholderAnalyzer):
    """직원 스테이크홀더 분석기"""
    
    def __init__(self):
        super().__init__(StakeholderType.EMPLOYEE)
        
        # 직원 특화 가중치 조정
        self.impact_weights = {
            "sentiment_intensity": 0.45,   # 직원 만족도가 가장 중요
            "volume": 0.2,                 # 언급량
            "trend": 0.25,                 # 만족도 변화 추이
            "keyword_relevance": 0.1       # 키워드 관련성
        }
    
    def get_specific_keywords(self) -> Dict[str, List[str]]:
        """직원 관련 특화 키워드"""
        return {
            "채용_인사": [
                "채용", "신입", "경력", "면접", "입사", "퇴사", "이직", "전직",
                "승진", "발탁", "인사", "발령", "배치", "전보", "순환"
            ],
            "급여_복지": [
                "급여", "연봉", "임금", "보너스", "성과급", "인센티브", "복지",
                "혜택", "보험", "연금", "휴가", "육아휴직", "병가", "수당"
            ],
            "근무환경": [
                "근무환경", "사무실", "시설", "장비", "도구", "환경", "분위기",
                "문화", "소통", "협업", "팀워크", "관계", "상사", "동료"
            ],
            "워라밸": [
                "워라밸", "워크라이프밸런스", "근무시간", "야근", "주말근무", "초과근무",
                "유연근무", "재택근무", "원격근무", "탄력근무", "시차출퇴근"
            ],
            "교육_성장": [
                "교육", "훈련", "연수", "세미나", "워크샵", "스킬업", "역량개발",
                "성장", "발전", "학습", "멘토링", "코칭", "피드백"
            ],
            "조직문화": [
                "조직문화", "기업문화", "회사문화", "소통", "투명성", "신뢰",
                "존중", "다양성", "포용", "혁신", "창의", "자율성", "책임"
            ],
            "스트레스_갈등": [
                "스트레스", "압박", "부담", "갈등", "마찰", "불만", "불평",
                "항의", "문제제기", "개선요구", "힘들다", "어렵다"
            ],
            "노사관계": [
                "노조", "노동조합", "단체협상", "파업", "쟁의", "협의", "합의",
                "노사", "사측", "노측", "대표", "위원회", "교섭"
            ]
        }
    
    def analyze_concerns(self, articles_data: List[Dict]) -> List[str]:
        """직원 주요 관심사 분석"""
        concerns = []
        keywords = self.get_specific_keywords()
        
        # 부정적 기사에서 주요 이슈 추출
        negative_articles = [
            article for article in articles_data 
            if article.get('sentiment_score') in ['negative', 'very_negative']
        ]
        
        concern_counts = Counter()
        
        # 부정적 기사 분석 (가중치 2배)
        for article in negative_articles:
            content = f"{article.get('title', '')} {article.get('content', '')}".lower()
            
            for category, words in keywords.items():
                if any(word in content for word in words):
                    concern_counts[category] += 2
        
        # 전체 기사 분석
        for article in articles_data:
            content = f"{article.get('title', '')} {article.get('content', '')}".lower()
            
            for category, words in keywords.items():
                if any(word in content for word in words):
                    concern_counts[category] += 1
        
        # 상위 관심사 추출
        top_concerns = concern_counts.most_common(5)
        concerns = [self._translate_concern(concern) for concern, count in top_concerns]
        
        # 특정 패턴 기반 관심사 추가
        all_content = " ".join([
            f"{article.get('title', '')} {article.get('content', '')}" 
            for article in articles_data
        ]).lower()
        
        # 구조조정 관련
        if any(word in all_content for word in ["구조조정", "정리해고", "명예퇴직", "희망퇴직"]):
            if "구조조정" not in concerns:
                concerns.append("구조조정")
        
        # 임금 관련
        if any(word in all_content for word in ["임금협상", "급여인상", "연봉협상"]):
            if "임금 협상" not in concerns:
                concerns.append("임금 협상")
        
        # 근무환경 관련
        if any(word in all_content for word in ["안전사고", "산업재해", "위험"]):
            if "안전 문제" not in concerns:
                concerns.append("안전 문제")
        
        return concerns[:5]
    
    def generate_action_items(self, insight: StakeholderInsight) -> List[str]:
        """직원 대상 권장 액션 아이템 생성"""
        actions = []
        
        # 센티멘트 기반 액션
        if insight.sentiment_score.value in ['negative', 'very_negative']:
            actions.extend([
                "직원 만족도 조사 즉시 실시",
                "경영진-직원 간담회 개최",
                "HR팀 직원 면담 강화",
                "내부 커뮤니케이션 채널 점검"
            ])
        elif insight.sentiment_score.value in ['positive', 'very_positive']:
            actions.extend([
                "우수 사례 전사 공유",
                "직원 인정 및 보상 프로그램 확대",
                "긍정적 조직문화 확산 활동"
            ])
        
        # 영향도 기반 액션
        if insight.impact_level.value in ['high', 'very_high']:
            actions.extend([
                "직원 센티멘트 주간 모니터링 실시",
                "부서별 분위기 점검 강화"
            ])
            
        # 긴급도 기반 액션
        if insight.urgency_level.value in ['high', 'critical']:
            actions.extend([
                "경영진 긴급 대응팀 구성",
                "노사 협의체 긴급 소집",
                "직원 대표와 즉시 면담"
            ])
        
        # 관심사 기반 액션
        for concern in insight.key_concerns:
            if "급여" in concern or "복지" in concern:
                actions.append("복리후생 제도 재검토 및 개선")
            elif "근무환경" in concern:
                actions.append("근무환경 개선 계획 수립")
            elif "워라밸" in concern:
                actions.append("유연근무제 확대 검토")
            elif "교육" in concern or "성장" in concern:
                actions.append("직원 교육 프로그램 강화")
            elif "조직문화" in concern:
                actions.append("조직문화 개선 TF 구성")
            elif "노사관계" in concern:
                actions.append("노사 소통 채널 정기화")
        
        # 부정 요인 기반 액션
        for factor in insight.negative_factors:
            if "스트레스_갈등" in factor:
                actions.append("직장 내 갈등 해결 프로그램 도입")
            elif "채용_인사" in factor:
                actions.append("인사 제도 투명성 강화")
        
        return list(set(actions))[:8]  # 중복 제거 후 상위 8개
    
    def get_description(self) -> str:
        """직원 스테이크홀더 설명"""
        return "기업에서 근무하는 모든 임직원으로, 기업의 생산성과 혁신의 원동력이며 조직문화와 기업 성과에 직접적인 영향을 미치는 핵심 스테이크홀더입니다."
    
    def get_key_metrics(self) -> List[str]:
        """직원 관련 주요 지표"""
        return [
            "직원 만족도",
            "직원 참여도 (Employee Engagement)",
            "이직률 (Turnover Rate)",
            "내부 추천 채용률",
            "교육 투자 비율",
            "승진율",
            "평균 근속년수",
            "워라밸 만족도",
            "조직문화 점수",
            "안전사고 발생률"
        ]
    
    def _translate_concern(self, concern_key: str) -> str:
        """관심사 키를 한국어로 번역"""
        translations = {
            "채용_인사": "채용 및 인사",
            "급여_복지": "급여 및 복지",
            "근무환경": "근무환경",
            "워라밸": "워라밸",
            "교육_성장": "교육 및 성장",
            "조직문화": "조직문화",
            "스트레스_갈등": "직장 내 갈등",
            "노사관계": "노사관계"
        }
        return translations.get(concern_key, concern_key)