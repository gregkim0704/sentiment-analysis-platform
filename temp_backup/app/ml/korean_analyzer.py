"""
한국어 특화 BERT 센티멘트 분석기
"""

import asyncio
import torch
import numpy as np
from typing import Dict, List, Optional, Any
from transformers import (
    AutoTokenizer, 
    AutoModelForSequenceClassification,
    pipeline
)
import re
from collections import Counter

from app.ml.base_analyzer import (
    BaseSentimentAnalyzer, 
    SentimentResult, 
    StakeholderResult,
    AnalysisInput,
    AnalysisConfidence
)
from app.core.logging import logger
from app.core.config import settings
from database.models import SentimentScore, StakeholderType


class KoreanSentimentAnalyzer(BaseSentimentAnalyzer):
    """한국어 특화 BERT 센티멘트 분석기"""
    
    def __init__(self):
        super().__init__("klue/bert-base")
        
        # 모델 관련 설정
        self.model_name = settings.SENTIMENT_MODEL_NAME
        self.max_length = settings.MAX_SEQUENCE_LENGTH
        self.batch_size = settings.BATCH_SIZE
        
        # 모델 컴포넌트
        self.tokenizer = None
        self.sentiment_model = None
        self.sentiment_pipeline = None
        
        # 디바이스 설정
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"사용 디바이스: {self.device}")
        
        # 스테이크홀더 분류를 위한 키워드 사전
        self.stakeholder_keywords = {
            StakeholderType.CUSTOMER: [
                "고객", "소비자", "구매자", "사용자", "이용자", "구입", "구매", "사용", "이용",
                "서비스", "품질", "만족", "불만", "후기", "리뷰", "평가", "경험", "사용법",
                "가격", "비용", "할인", "프로모션", "이벤트", "혜택", "배송", "교환", "환불"
            ],
            StakeholderType.INVESTOR: [
                "투자자", "주주", "투자", "주식", "주가", "수익", "배당", "실적", "매출", "영업이익",
                "순이익", "성장", "전망", "목표주가", "분석", "리포트", "펀드", "기관투자자",
                "개인투자자", "증권", "거래", "상장", "공모", "IPO", "M&A", "인수합병"
            ],
            StakeholderType.EMPLOYEE: [
                "직원", "임직원", "사원", "근로자", "노동자", "인사", "채용", "퇴사", "승진",
                "연봉", "급여", "복지", "근무환경", "워라밸", "조직문화", "교육", "훈련",
                "노조", "파업", "단체협상", "근무시간", "휴가", "출장", "재택근무", "복지"
            ],
            StakeholderType.GOVERNMENT: [
                "정부", "정책", "규제", "법률", "제도", "허가", "승인", "감독", "점검", "조사",
                "과태료", "제재", "처벌", "법안", "개정", "시행", "공공", "국가", "지자체",
                "부처", "청", "위원회", "감사원", "국정감사", "세금", "세제", "지원금", "보조금"
            ],
            StakeholderType.MEDIA: [
                "언론", "기자", "보도", "뉴스", "기사", "취재", "인터뷰", "발표", "공시",
                "보도자료", "브리핑", "컨퍼런스", "미디어", "방송", "신문", "잡지", "온라인",
                "소셜미디어", "SNS", "블로그", "유튜브", "팟캐스트", "라이브", "중계"
            ],
            StakeholderType.PARTNER: [
                "파트너", "협력사", "공급업체", "벤더", "계약", "협약", "제휴", "파트너십",
                "공급", "납품", "조달", "외주", "아웃소싱", "협력", "동반성장", "상생",
                "계약서", "MOU", "업무협약", "전략적제휴", "조인트벤처", "컨소시엄"
            ],
            StakeholderType.COMPETITOR: [
                "경쟁사", "경쟁업체", "라이벌", "경쟁", "시장점유율", "순위", "비교", "대비",
                "차별화", "우위", "열세", "추격", "선두", "2위", "3위", "업계", "동종업계",
                "벤치마킹", "모방", "카피", "유사", "대체", "경쟁력", "경쟁우위"
            ],
            StakeholderType.COMMUNITY: [
                "지역사회", "커뮤니티", "주민", "시민", "지역", "동네", "마을", "사회공헌",
                "CSR", "봉사", "기부", "후원", "환경", "친환경", "지속가능", "ESG",
                "사회적책임", "공익", "나눔", "상생", "지역경제", "일자리", "고용창출"
            ]
        }
        
        # 감정 키워드 사전
        self.sentiment_keywords = {
            SentimentScore.VERY_POSITIVE: [
                "최고", "훌륭", "완벽", "탁월", "뛰어난", "우수", "좋은", "만족", "성공",
                "성과", "혁신", "발전", "성장", "개선", "향상", "증가", "상승", "호조"
            ],
            SentimentScore.POSITIVE: [
                "좋다", "괜찮다", "나쁘지않다", "긍정적", "희망적", "기대", "관심", "추천",
                "도움", "유용", "편리", "효과적", "안정적", "신뢰", "품질"
            ],
            SentimentScore.NEUTRAL: [
                "보통", "일반적", "평범", "무난", "그저그런", "평가", "분석", "검토",
                "확인", "점검", "조사", "연구", "개발", "계획", "예정"
            ],
            SentimentScore.NEGATIVE: [
                "나쁘다", "부족", "문제", "이슈", "우려", "걱정", "불안", "실망", "아쉽다",
                "개선필요", "부정적", "하락", "감소", "악화", "지연", "취소"
            ],
            SentimentScore.VERY_NEGATIVE: [
                "최악", "끔찍", "심각", "위험", "위기", "실패", "파산", "손실", "피해",
                "사고", "문제발생", "중단", "폐지", "철회", "거부", "반대", "항의"
            ]
        }
    
    async def load_model(self) -> bool:
        """모델 로드"""
        try:
            logger.info(f"한국어 센티멘트 분석 모델 로드 시작: {self.model_name}")
            
            # 토크나이저 로드
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                cache_dir=settings.SENTIMENT_MODEL_PATH
            )
            
            # 센티멘트 분석 파이프라인 생성 (사전 훈련된 모델 사용)
            try:
                self.sentiment_pipeline = pipeline(
                    "sentiment-analysis",
                    model=self.model_name,
                    tokenizer=self.tokenizer,
                    device=0 if torch.cuda.is_available() else -1,
                    return_all_scores=True
                )
                logger.info("사전 훈련된 센티멘트 모델 로드 성공")
            except Exception as e:
                logger.warning(f"사전 훈련된 모델 로드 실패, 기본 모델 사용: {e}")
                # 기본 BERT 모델로 대체
                self.sentiment_model = AutoModelForSequenceClassification.from_pretrained(
                    self.model_name,
                    num_labels=5,  # 5단계 감정
                    cache_dir=settings.SENTIMENT_MODEL_PATH
                )
                self.sentiment_model.to(self.device)
                self.sentiment_model.eval()
            
            self.is_loaded = True
            logger.info("한국어 센티멘트 분석 모델 로드 완료")
            return True
            
        except Exception as e:
            logger.error(f"모델 로드 실패: {e}")
            self.is_loaded = False
            return False
    
    async def analyze_sentiment(self, text_input: AnalysisInput) -> SentimentResult:
        """센티멘트 분석"""
        if not self.is_loaded:
            await self.load_model()
        
        try:
            # 텍스트 전처리
            text = self.preprocess_text(text_input.get_full_text())
            
            if not text:
                return self._create_default_sentiment_result("빈 텍스트")
            
            # 키워드 기반 사전 분석
            keyword_sentiment = self._analyze_by_keywords(text)
            
            # 모델 기반 분석
            if self.sentiment_pipeline:
                model_sentiment = await self._analyze_with_pipeline(text)
            else:
                model_sentiment = await self._analyze_with_model(text)
            
            # 결과 통합
            final_result = self._combine_sentiment_results(
                keyword_sentiment, 
                model_sentiment, 
                text_input
            )
            
            return final_result
            
        except Exception as e:
            logger.error(f"센티멘트 분석 오류: {e}")
            return self._create_default_sentiment_result(f"분석 오류: {str(e)}")
    
    async def classify_stakeholder(self, text_input: AnalysisInput) -> StakeholderResult:
        """스테이크홀더 분류"""
        try:
            text = self.preprocess_text(text_input.get_full_text())
            
            if not text:
                return self._create_default_stakeholder_result("빈 텍스트")
            
            # 키워드 기반 분류
            stakeholder_scores = {}
            
            for stakeholder_type, keywords in self.stakeholder_keywords.items():
                score = 0
                matched_keywords = []
                
                for keyword in keywords:
                    count = text.lower().count(keyword)
                    if count > 0:
                        score += count
                        matched_keywords.append(keyword)
                
                # 정규화 (텍스트 길이 고려)
                normalized_score = score / max(len(text.split()), 1) * 100
                stakeholder_scores[stakeholder_type] = {
                    "score": normalized_score,
                    "matched_keywords": matched_keywords
                }
            
            # 최고 점수 스테이크홀더 선택
            if stakeholder_scores:
                best_stakeholder = max(
                    stakeholder_scores.keys(), 
                    key=lambda x: stakeholder_scores[x]["score"]
                )
                best_score = stakeholder_scores[best_stakeholder]["score"]
                
                # 신뢰도 계산
                total_score = sum(data["score"] for data in stakeholder_scores.values())
                confidence = best_score / max(total_score, 1) if total_score > 0 else 0
                
                # 확률 분포 계산
                probabilities = {}
                for stakeholder_type, data in stakeholder_scores.items():
                    prob = data["score"] / max(total_score, 1) if total_score > 0 else 0
                    probabilities[stakeholder_type.value] = round(prob, 3)
                
                # 추론 근거 생성
                matched_keywords = stakeholder_scores[best_stakeholder]["matched_keywords"]
                reasoning = f"매칭된 키워드: {', '.join(matched_keywords[:5])}" if matched_keywords else "키워드 매칭 없음"
                
                return StakeholderResult(
                    stakeholder_type=best_stakeholder,
                    confidence=min(confidence, 1.0),
                    probabilities=probabilities,
                    reasoning=reasoning
                )
            else:
                # 기본값: 언론으로 분류
                return self._create_default_stakeholder_result("키워드 매칭 실패")
                
        except Exception as e:
            logger.error(f"스테이크홀더 분류 오류: {e}")
            return self._create_default_stakeholder_result(f"분류 오류: {str(e)}")
    
    def _analyze_by_keywords(self, text: str) -> Dict[str, Any]:
        """키워드 기반 센티멘트 분석"""
        sentiment_scores = {}
        
        for sentiment, keywords in self.sentiment_keywords.items():
            score = 0
            for keyword in keywords:
                score += text.lower().count(keyword)
            sentiment_scores[sentiment] = score
        
        # 최고 점수 감정 선택
        if any(sentiment_scores.values()):
            best_sentiment = max(sentiment_scores.keys(), key=lambda x: sentiment_scores[x])
            total_score = sum(sentiment_scores.values())
            confidence = sentiment_scores[best_sentiment] / max(total_score, 1)
            
            return {
                "sentiment": best_sentiment,
                "confidence": confidence,
                "method": "keyword"
            }
        
        return {
            "sentiment": SentimentScore.NEUTRAL,
            "confidence": 0.0,
            "method": "keyword"
        }
    
    async def _analyze_with_pipeline(self, text: str) -> Dict[str, Any]:
        """파이프라인을 사용한 센티멘트 분석"""
        try:
            # 텍스트 길이 제한
            if len(text) > self.max_length:
                text = text[:self.max_length]
            
            # 비동기 실행을 위해 별도 스레드에서 실행
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None, 
                self.sentiment_pipeline, 
                text
            )
            
            if results and len(results) > 0:
                # 결과 파싱 (모델에 따라 다를 수 있음)
                scores = results[0] if isinstance(results[0], list) else results
                
                # 라벨을 센티멘트로 매핑
                sentiment_mapping = {
                    "NEGATIVE": SentimentScore.NEGATIVE,
                    "POSITIVE": SentimentScore.POSITIVE,
                    "NEUTRAL": SentimentScore.NEUTRAL,
                    "LABEL_0": SentimentScore.VERY_NEGATIVE,
                    "LABEL_1": SentimentScore.NEGATIVE,
                    "LABEL_2": SentimentScore.NEUTRAL,
                    "LABEL_3": SentimentScore.POSITIVE,
                    "LABEL_4": SentimentScore.VERY_POSITIVE,
                }
                
                best_result = max(scores, key=lambda x: x['score'])
                sentiment = sentiment_mapping.get(best_result['label'], SentimentScore.NEUTRAL)
                
                return {
                    "sentiment": sentiment,
                    "confidence": best_result['score'],
                    "method": "pipeline",
                    "all_scores": scores
                }
            
        except Exception as e:
            logger.error(f"파이프라인 분석 오류: {e}")
        
        return {
            "sentiment": SentimentScore.NEUTRAL,
            "confidence": 0.0,
            "method": "pipeline"
        }
    
    async def _analyze_with_model(self, text: str) -> Dict[str, Any]:
        """직접 모델을 사용한 센티멘트 분석"""
        try:
            # 토큰화
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                max_length=self.max_length,
                truncation=True,
                padding=True
            )
            
            # GPU로 이동
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # 예측
            with torch.no_grad():
                outputs = self.sentiment_model(**inputs)
                probabilities = torch.softmax(outputs.logits, dim=-1)
                predicted_class = torch.argmax(probabilities, dim=-1).item()
                confidence = probabilities[0][predicted_class].item()
            
            # 클래스를 센티멘트로 매핑
            sentiment_classes = [
                SentimentScore.VERY_NEGATIVE,
                SentimentScore.NEGATIVE,
                SentimentScore.NEUTRAL,
                SentimentScore.POSITIVE,
                SentimentScore.VERY_POSITIVE
            ]
            
            sentiment = sentiment_classes[predicted_class]
            
            return {
                "sentiment": sentiment,
                "confidence": confidence,
                "method": "model"
            }
            
        except Exception as e:
            logger.error(f"모델 분석 오류: {e}")
            return {
                "sentiment": SentimentScore.NEUTRAL,
                "confidence": 0.0,
                "method": "model"
            }
    
    def _combine_sentiment_results(
        self, 
        keyword_result: Dict[str, Any], 
        model_result: Dict[str, Any],
        text_input: AnalysisInput
    ) -> SentimentResult:
        """키워드와 모델 결과 통합"""
        
        # 가중 평균으로 결과 통합
        keyword_weight = 0.3
        model_weight = 0.7
        
        # 신뢰도가 높은 결과에 더 큰 가중치
        if keyword_result["confidence"] > model_result["confidence"]:
            keyword_weight = 0.6
            model_weight = 0.4
        
        # 최종 센티멘트 결정
        if keyword_result["confidence"] > 0.7:
            final_sentiment = keyword_result["sentiment"]
            final_confidence = keyword_result["confidence"]
        elif model_result["confidence"] > 0.7:
            final_sentiment = model_result["sentiment"]
            final_confidence = model_result["confidence"]
        else:
            # 둘 다 신뢰도가 낮으면 중립
            final_sentiment = SentimentScore.NEUTRAL
            final_confidence = (keyword_result["confidence"] + model_result["confidence"]) / 2
        
        # 확률 분포 생성
        probabilities = {}
        for sentiment in SentimentScore:
            if sentiment == final_sentiment:
                probabilities[sentiment.value] = final_confidence
            else:
                probabilities[sentiment.value] = (1 - final_confidence) / 4
        
        # 키워드 추출
        keywords = self.extract_keywords(text_input.get_full_text())
        
        # 추론 근거 생성
        reasoning = f"키워드 분석: {keyword_result['method']} (신뢰도: {keyword_result['confidence']:.2f}), " \
                   f"모델 분석: {model_result['method']} (신뢰도: {model_result['confidence']:.2f})"
        
        return SentimentResult(
            sentiment_score=final_sentiment,
            confidence=final_confidence,
            confidence_level=self.get_confidence_level(final_confidence),
            probabilities=probabilities,
            keywords=keywords,
            reasoning=reasoning
        )
    
    def _create_default_sentiment_result(self, reason: str) -> SentimentResult:
        """기본 센티멘트 결과 생성"""
        return SentimentResult(
            sentiment_score=SentimentScore.NEUTRAL,
            confidence=0.0,
            confidence_level=AnalysisConfidence.VERY_LOW,
            probabilities={sentiment.value: 0.2 for sentiment in SentimentScore},
            keywords=[],
            reasoning=reason
        )
    
    def _create_default_stakeholder_result(self, reason: str) -> StakeholderResult:
        """기본 스테이크홀더 결과 생성"""
        return StakeholderResult(
            stakeholder_type=StakeholderType.MEDIA,
            confidence=0.0,
            probabilities={stakeholder.value: 1/len(StakeholderType) for stakeholder in StakeholderType},
            reasoning=reason
        )