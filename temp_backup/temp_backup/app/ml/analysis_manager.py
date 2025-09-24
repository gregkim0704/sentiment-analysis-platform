"""
센티멘트 분석 매니저
"""

import asyncio
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.ml.base_analyzer import BaseSentimentAnalyzer, AnalysisInput
from app.ml.korean_analyzer import KoreanSentimentAnalyzer
from app.core.database import get_db
from app.core.logging import logger
from app.core.config import settings
from database.models import (
    NewsArticle, Company, SentimentTrend, 
    SentimentScore, StakeholderType, NewsSource
)


class SentimentAnalysisManager:
    """센티멘트 분석 매니저"""
    
    def __init__(self):
        self.analyzer: BaseSentimentAnalyzer = KoreanSentimentAnalyzer()
        self.batch_size = settings.BATCH_SIZE
        self.confidence_threshold = settings.SENTIMENT_CONFIDENCE_THRESHOLD
        self.max_concurrent_analyses = 5
    
    async def initialize(self) -> bool:
        """분석기 초기화"""
        try:
            logger.info("센티멘트 분석 매니저 초기화 시작")
            success = await self.analyzer.load_model()
            
            if success:
                logger.info("센티멘트 분석 매니저 초기화 완료")
            else:
                logger.error("센티멘트 분석 매니저 초기화 실패")
            
            return success
            
        except Exception as e:
            logger.error(f"센티멘트 분석 매니저 초기화 오류: {e}")
            return False
    
    async def analyze_pending_articles(self, limit: int = 100) -> Dict[str, Any]:
        """센티멘트 분석이 필요한 기사들 처리"""
        logger.info(f"대기 중인 기사 센티멘트 분석 시작 (최대 {limit}개)")
        
        db = next(get_db())
        
        try:
            # 분석이 필요한 기사들 조회
            pending_articles = db.query(NewsArticle).filter(
                NewsArticle.sentiment_score.is_(None)
            ).limit(limit).all()
            
            if not pending_articles:
                logger.info("분석할 기사가 없습니다")
                return {
                    "success": True,
                    "processed_count": 0,
                    "message": "분석할 기사가 없습니다"
                }
            
            logger.info(f"분석 대상 기사: {len(pending_articles)}개")
            
            # 분석 입력 데이터 준비
            analysis_inputs = []
            for article in pending_articles:
                company = db.query(Company).filter(Company.id == article.company_id).first()
                company_name = company.name if company else "Unknown"
                
                analysis_input = AnalysisInput(
                    title=article.title or "",
                    content=article.content or "",
                    company_name=company_name,
                    author=article.author,
                    source=article.source.value if article.source else None,
                    url=article.url
                )
                analysis_inputs.append((article, analysis_input))
            
            # 배치 분석 실행
            processed_count = 0
            failed_count = 0
            
            # 세마포어로 동시 분석 수 제한
            semaphore = asyncio.Semaphore(self.max_concurrent_analyses)
            
            async def analyze_batch(batch_data):
                async with semaphore:
                    return await self._process_article_batch(batch_data, db)
            
            # 배치별로 처리
            for i in range(0, len(analysis_inputs), self.batch_size):
                batch = analysis_inputs[i:i + self.batch_size]
                
                try:
                    batch_result = await analyze_batch(batch)
                    processed_count += batch_result["processed"]
                    failed_count += batch_result["failed"]
                    
                    # 배치 간 잠시 대기
                    if i + self.batch_size < len(analysis_inputs):
                        await asyncio.sleep(0.5)
                        
                except Exception as e:
                    logger.error(f"배치 처리 오류: {e}")
                    failed_count += len(batch)
            
            # 최종 커밋
            db.commit()
            
            logger.info(f"센티멘트 분석 완료 - 성공: {processed_count}개, 실패: {failed_count}개")
            
            return {
                "success": True,
                "processed_count": processed_count,
                "failed_count": failed_count,
                "total_articles": len(pending_articles)
            }
            
        except Exception as e:
            logger.error(f"센티멘트 분석 처리 오류: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "processed_count": 0
            }
        finally:
            db.close()
    
    async def _process_article_batch(
        self, 
        batch_data: List[Tuple[NewsArticle, AnalysisInput]], 
        db: Session
    ) -> Dict[str, int]:
        """기사 배치 처리"""
        processed = 0
        failed = 0
        
        try:
            # 분석 입력만 추출
            inputs = [data[1] for data in batch_data]
            
            # 배치 분석 실행
            results = await self.analyzer.batch_analyze(inputs, len(inputs))
            
            # 결과를 데이터베이스에 저장
            for (article, _), (sentiment_result, stakeholder_result) in zip(batch_data, results):
                try:
                    # 센티멘트 분석 결과 저장
                    article.sentiment_score = sentiment_result.sentiment_score
                    article.sentiment_confidence = sentiment_result.confidence
                    article.stakeholder_type = stakeholder_result.stakeholder_type
                    
                    # 키워드 업데이트 (기존 키워드와 병합)
                    existing_keywords = article.keywords or []
                    new_keywords = sentiment_result.keywords
                    combined_keywords = list(set(existing_keywords + new_keywords))
                    article.keywords = combined_keywords[:20]  # 최대 20개로 제한
                    
                    processed += 1
                    
                except Exception as e:
                    logger.error(f"기사 업데이트 오류 (ID: {article.id}): {e}")
                    failed += 1
            
            return {"processed": processed, "failed": failed}
            
        except Exception as e:
            logger.error(f"배치 분석 오류: {e}")
            return {"processed": 0, "failed": len(batch_data)}
    
    async def analyze_single_article(
        self, 
        article_id: int, 
        db: Session = None
    ) -> Dict[str, Any]:
        """단일 기사 센티멘트 분석"""
        if db is None:
            db = next(get_db())
            should_close_db = True
        else:
            should_close_db = False
        
        try:
            # 기사 조회
            article = db.query(NewsArticle).filter(NewsArticle.id == article_id).first()
            if not article:
                return {
                    "success": False,
                    "error": "기사를 찾을 수 없습니다"
                }
            
            # 회사 정보 조회
            company = db.query(Company).filter(Company.id == article.company_id).first()
            company_name = company.name if company else "Unknown"
            
            # 분석 입력 준비
            analysis_input = AnalysisInput(
                title=article.title or "",
                content=article.content or "",
                company_name=company_name,
                author=article.author,
                source=article.source.value if article.source else None,
                url=article.url
            )
            
            # 분석 실행
            sentiment_result = await self.analyzer.analyze_sentiment(analysis_input)
            stakeholder_result = await self.analyzer.classify_stakeholder(analysis_input)
            
            # 결과 저장
            article.sentiment_score = sentiment_result.sentiment_score
            article.sentiment_confidence = sentiment_result.confidence
            article.stakeholder_type = stakeholder_result.stakeholder_type
            
            # 키워드 업데이트
            existing_keywords = article.keywords or []
            new_keywords = sentiment_result.keywords
            combined_keywords = list(set(existing_keywords + new_keywords))
            article.keywords = combined_keywords[:20]
            
            db.commit()
            
            logger.info(f"기사 분석 완료 (ID: {article_id})")
            
            return {
                "success": True,
                "article_id": article_id,
                "sentiment_result": sentiment_result.to_dict(),
                "stakeholder_result": stakeholder_result.to_dict()
            }
            
        except Exception as e:
            logger.error(f"단일 기사 분석 오류 (ID: {article_id}): {e}")
            if db:
                db.rollback()
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            if should_close_db:
                db.close()
    
    async def aggregate_daily_trends(self, target_date: datetime = None) -> Dict[str, Any]:
        """일별 센티멘트 트렌드 집계"""
        if target_date is None:
            target_date = datetime.now().date()
        else:
            target_date = target_date.date()
        
        logger.info(f"일별 센티멘트 트렌드 집계 시작: {target_date}")
        
        db = next(get_db())
        
        try:
            # 해당 날짜의 기사들 조회
            start_datetime = datetime.combine(target_date, datetime.min.time())
            end_datetime = datetime.combine(target_date, datetime.max.time())
            
            articles = db.query(NewsArticle).filter(
                and_(
                    NewsArticle.published_date >= start_datetime,
                    NewsArticle.published_date <= end_datetime,
                    NewsArticle.sentiment_score.isnot(None),
                    NewsArticle.stakeholder_type.isnot(None)
                )
            ).all()
            
            if not articles:
                logger.info(f"집계할 기사가 없습니다: {target_date}")
                return {
                    "success": True,
                    "date": target_date.isoformat(),
                    "aggregated_trends": 0
                }
            
            # 회사별, 스테이크홀더별로 그룹화
            trend_data = {}
            
            for article in articles:
                key = (article.company_id, article.stakeholder_type)
                
                if key not in trend_data:
                    trend_data[key] = {
                        "company_id": article.company_id,
                        "stakeholder_type": article.stakeholder_type,
                        "articles": [],
                        "sentiment_scores": [],
                        "keywords": []
                    }
                
                trend_data[key]["articles"].append(article)
                
                # 센티멘트 점수를 숫자로 변환
                sentiment_numeric = self._sentiment_to_numeric(article.sentiment_score)
                trend_data[key]["sentiment_scores"].append(sentiment_numeric)
                
                # 키워드 수집
                if article.keywords:
                    trend_data[key]["keywords"].extend(article.keywords)
            
            # 트렌드 데이터 생성 및 저장
            aggregated_count = 0
            
            for (company_id, stakeholder_type), data in trend_data.items():
                try:
                    # 기존 트렌드 데이터 확인
                    existing_trend = db.query(SentimentTrend).filter(
                        and_(
                            SentimentTrend.company_id == company_id,
                            SentimentTrend.stakeholder_type == stakeholder_type,
                            func.date(SentimentTrend.date) == target_date
                        )
                    ).first()
                    
                    # 통계 계산
                    total_articles = len(data["articles"])
                    sentiment_scores = data["sentiment_scores"]
                    
                    positive_count = sum(1 for score in sentiment_scores if score > 0)
                    negative_count = sum(1 for score in sentiment_scores if score < 0)
                    neutral_count = sum(1 for score in sentiment_scores if score == 0)
                    
                    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
                    import numpy as np
                    sentiment_volatility = np.std(sentiment_scores) if len(sentiment_scores) > 1 else 0.0
                    
                    # 상위 키워드 추출
                    from collections import Counter
                    keyword_counts = Counter(data["keywords"])
                    top_keywords = [word for word, count in keyword_counts.most_common(10)]
                    
                    if existing_trend:
                        # 기존 데이터 업데이트
                        existing_trend.total_articles = total_articles
                        existing_trend.positive_count = positive_count
                        existing_trend.negative_count = negative_count
                        existing_trend.neutral_count = neutral_count
                        existing_trend.avg_sentiment_score = avg_sentiment
                        existing_trend.sentiment_volatility = sentiment_volatility
                        existing_trend.top_keywords = top_keywords
                    else:
                        # 새 트렌드 데이터 생성
                        new_trend = SentimentTrend(
                            company_id=company_id,
                            stakeholder_type=stakeholder_type,
                            date=start_datetime,
                            total_articles=total_articles,
                            positive_count=positive_count,
                            negative_count=negative_count,
                            neutral_count=neutral_count,
                            avg_sentiment_score=avg_sentiment,
                            sentiment_volatility=sentiment_volatility,
                            top_keywords=top_keywords
                        )
                        db.add(new_trend)
                    
                    aggregated_count += 1
                    
                except Exception as e:
                    logger.error(f"트렌드 집계 오류 (회사: {company_id}, 스테이크홀더: {stakeholder_type}): {e}")
                    continue
            
            db.commit()
            
            logger.info(f"일별 트렌드 집계 완료: {aggregated_count}개 트렌드")
            
            return {
                "success": True,
                "date": target_date.isoformat(),
                "total_articles": len(articles),
                "aggregated_trends": aggregated_count
            }
            
        except Exception as e:
            logger.error(f"일별 트렌드 집계 오류: {e}")
            db.rollback()
            return {
                "success": False,
                "error": str(e),
                "aggregated_trends": 0
            }
        finally:
            db.close()
    
    def _sentiment_to_numeric(self, sentiment: SentimentScore) -> int:
        """센티멘트를 숫자로 변환"""
        mapping = {
            SentimentScore.VERY_NEGATIVE: -2,
            SentimentScore.NEGATIVE: -1,
            SentimentScore.NEUTRAL: 0,
            SentimentScore.POSITIVE: 1,
            SentimentScore.VERY_POSITIVE: 2
        }
        return mapping.get(sentiment, 0)
    
    async def get_analysis_statistics(self, days: int = 30) -> Dict[str, Any]:
        """분석 통계 조회"""
        db = next(get_db())
        
        try:
            since_date = datetime.now() - timedelta(days=days)
            
            # 전체 기사 수
            total_articles = db.query(func.count(NewsArticle.id)).scalar()
            
            # 분석된 기사 수
            analyzed_articles = db.query(func.count(NewsArticle.id)).filter(
                NewsArticle.sentiment_score.isnot(None)
            ).scalar()
            
            # 최근 분석된 기사 수
            recent_analyzed = db.query(func.count(NewsArticle.id)).filter(
                and_(
                    NewsArticle.sentiment_score.isnot(None),
                    NewsArticle.collected_date >= since_date
                )
            ).scalar()
            
            # 센티멘트 분포
            sentiment_distribution = {}
            for sentiment in SentimentScore:
                count = db.query(func.count(NewsArticle.id)).filter(
                    NewsArticle.sentiment_score == sentiment
                ).scalar()
                sentiment_distribution[sentiment.value] = count
            
            # 스테이크홀더 분포
            stakeholder_distribution = {}
            for stakeholder in StakeholderType:
                count = db.query(func.count(NewsArticle.id)).filter(
                    NewsArticle.stakeholder_type == stakeholder
                ).scalar()
                stakeholder_distribution[stakeholder.value] = count
            
            # 분석 완료율
            completion_rate = (analyzed_articles / total_articles * 100) if total_articles > 0 else 0
            
            return {
                "period_days": days,
                "total_articles": total_articles,
                "analyzed_articles": analyzed_articles,
                "recent_analyzed": recent_analyzed,
                "completion_rate": round(completion_rate, 2),
                "sentiment_distribution": sentiment_distribution,
                "stakeholder_distribution": stakeholder_distribution,
                "analyzer_info": self.analyzer.get_model_info()
            }
            
        except Exception as e:
            logger.error(f"분석 통계 조회 오류: {e}")
            return {"error": str(e)}
        finally:
            db.close()


# 전역 분석 매니저 인스턴스
analysis_manager = SentimentAnalysisManager()


def get_analysis_manager() -> SentimentAnalysisManager:
    """분석 매니저 의존성 주입"""
    return analysis_manager