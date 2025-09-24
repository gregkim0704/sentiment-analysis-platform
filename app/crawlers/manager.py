"""
크롤링 매니저 - 모든 크롤러를 통합 관리
"""

import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.crawlers.base import BaseCrawler, NewsArticle
from app.crawlers.naver_crawler import NaverNewsCrawler
from app.crawlers.daum_crawler import DaumNewsCrawler
from app.crawlers.google_crawler import GoogleNewsCrawler
from app.core.database import get_db
from app.core.logging import logger
from app.core.config import settings
from database.models import (
    Company, NewsArticle as DBNewsArticle, CrawlingJob, 
    NewsSource, StakeholderType, SentimentScore
)


class CrawlingManager:
    """크롤링 매니저"""
    
    def __init__(self):
        self.crawlers: Dict[NewsSource, BaseCrawler] = {
            NewsSource.NAVER: NaverNewsCrawler(),
            NewsSource.DAUM: DaumNewsCrawler(),
            NewsSource.GOOGLE: GoogleNewsCrawler(),
        }
        self.max_concurrent_crawlers = 3
        self.default_days_back = 7
    
    async def crawl_all_companies(self, days_back: int = None) -> Dict[str, Any]:
        """모든 회사의 뉴스 크롤링"""
        days_back = days_back or self.default_days_back
        
        logger.info(f"전체 회사 뉴스 크롤링 시작 (최근 {days_back}일)")
        
        # 데이터베이스 세션 생성
        db = next(get_db())
        
        try:
            # 활성 회사 목록 조회
            companies = db.query(Company).filter(Company.is_active == True).all()
            
            if not companies:
                logger.warning("활성 회사가 없습니다")
                return {"success": False, "message": "활성 회사가 없습니다"}
            
            logger.info(f"크롤링 대상 회사: {len(companies)}개")
            
            # 회사별 크롤링 실행
            total_articles = 0
            company_results = {}
            
            for company in companies:
                try:
                    result = await self.crawl_company_news(company, days_back, db)
                    company_results[company.name] = result
                    total_articles += result.get('articles_saved', 0)
                    
                    # 회사 간 지연
                    await asyncio.sleep(2)
                    
                except Exception as e:
                    logger.error(f"회사 크롤링 오류 ({company.name}): {e}")
                    company_results[company.name] = {
                        "success": False,
                        "error": str(e),
                        "articles_saved": 0
                    }
            
            logger.info(f"전체 크롤링 완료 - 총 {total_articles}개 기사 수집")
            
            return {
                "success": True,
                "total_companies": len(companies),
                "total_articles": total_articles,
                "company_results": company_results,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"전체 크롤링 오류: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_articles": 0
            }
        finally:
            db.close()
    
    async def crawl_company_news(
        self, 
        company: Company, 
        days_back: int = None,
        db: Session = None
    ) -> Dict[str, Any]:
        """특정 회사의 뉴스 크롤링"""
        days_back = days_back or self.default_days_back
        
        if db is None:
            db = next(get_db())
            should_close_db = True
        else:
            should_close_db = False
        
        logger.info(f"회사 뉴스 크롤링 시작: {company.name}")
        
        try:
            # 크롤링 작업 로그 생성
            crawling_jobs = []
            for source in self.crawlers.keys():
                job = CrawlingJob(
                    company_id=company.id,
                    source=source,
                    status="running"
                )
                db.add(job)
                crawling_jobs.append(job)
            
            db.commit()
            
            # 모든 크롤러로 동시 크롤링
            crawler_tasks = []
            for source, crawler in self.crawlers.items():
                task = self._crawl_with_crawler(crawler, company, days_back)
                crawler_tasks.append(task)
            
            # 크롤러별 결과 수집
            crawler_results = await asyncio.gather(*crawler_tasks, return_exceptions=True)
            
            # 결과 통합 및 저장
            all_articles = []
            source_results = {}
            
            for i, (source, result) in enumerate(zip(self.crawlers.keys(), crawler_results)):
                job = crawling_jobs[i]
                
                if isinstance(result, Exception):
                    logger.error(f"크롤러 오류 ({source.value}): {result}")
                    job.status = "failed"
                    job.error_message = str(result)
                    source_results[source.value] = {
                        "success": False,
                        "error": str(result),
                        "articles": 0
                    }
                else:
                    articles = result or []
                    all_articles.extend(articles)
                    job.status = "completed"
                    job.articles_found = len(articles)
                    job.articles_processed = len(articles)
                    source_results[source.value] = {
                        "success": True,
                        "articles": len(articles)
                    }
                
                job.end_time = datetime.now()
                db.commit()
            
            # 중복 제거 (URL 기준)
            unique_articles = self._remove_duplicates(all_articles)
            
            # 데이터베이스에 저장
            saved_count = await self._save_articles_to_db(unique_articles, company, db)
            
            # 작업 로그 업데이트
            for job in crawling_jobs:
                job.articles_saved = saved_count // len(crawling_jobs)  # 균등 분배
            
            db.commit()
            
            logger.info(f"회사 크롤링 완료 ({company.name}): {saved_count}개 기사 저장")
            
            return {
                "success": True,
                "company_name": company.name,
                "articles_found": len(all_articles),
                "articles_unique": len(unique_articles),
                "articles_saved": saved_count,
                "source_results": source_results,
                "completed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"회사 크롤링 오류 ({company.name}): {e}")
            
            # 실패한 작업들 상태 업데이트
            for job in crawling_jobs:
                if job.status == "running":
                    job.status = "failed"
                    job.error_message = str(e)
                    job.end_time = datetime.now()
            
            db.commit()
            
            return {
                "success": False,
                "company_name": company.name,
                "error": str(e),
                "articles_saved": 0
            }
        finally:
            if should_close_db:
                db.close()
    
    async def _crawl_with_crawler(
        self, 
        crawler: BaseCrawler, 
        company: Company, 
        days_back: int
    ) -> List[NewsArticle]:
        """특정 크롤러로 크롤링 실행"""
        try:
            async with crawler:
                articles = await crawler.crawl_company_news(company, days_back)
                return articles
        except Exception as e:
            logger.error(f"크롤러 실행 오류 ({crawler.source.value}): {e}")
            raise
    
    def _remove_duplicates(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """중복 기사 제거 (URL 기준)"""
        seen_urls = set()
        unique_articles = []
        
        for article in articles:
            if article.url not in seen_urls:
                seen_urls.add(article.url)
                unique_articles.append(article)
        
        logger.info(f"중복 제거: {len(articles)}개 → {len(unique_articles)}개")
        return unique_articles
    
    async def _save_articles_to_db(
        self, 
        articles: List[NewsArticle], 
        company: Company, 
        db: Session
    ) -> int:
        """기사를 데이터베이스에 저장"""
        saved_count = 0
        
        for article in articles:
            try:
                # 이미 존재하는 기사인지 확인
                existing = db.query(DBNewsArticle).filter(
                    DBNewsArticle.url == article.url
                ).first()
                
                if existing:
                    logger.debug(f"이미 존재하는 기사: {article.url}")
                    continue
                
                # 새 기사 생성
                db_article = DBNewsArticle(
                    company_id=company.id,
                    title=article.title,
                    content=article.content,
                    url=article.url,
                    source=article.source,
                    author=article.author,
                    published_date=article.published_date or datetime.now(),
                    keywords=article.keywords,
                    summary=article.summary,
                    # 센티멘트 분석은 별도 프로세스에서 수행
                    sentiment_score=None,
                    sentiment_confidence=None,
                    stakeholder_type=None
                )
                
                db.add(db_article)
                saved_count += 1
                
                # 배치 커밋 (100개씩)
                if saved_count % 100 == 0:
                    db.commit()
                    logger.info(f"중간 저장: {saved_count}개 기사")
                
            except Exception as e:
                logger.error(f"기사 저장 오류: {e}")
                db.rollback()
                continue
        
        # 최종 커밋
        try:
            db.commit()
            logger.info(f"기사 저장 완료: {saved_count}개")
        except Exception as e:
            logger.error(f"최종 커밋 오류: {e}")
            db.rollback()
            saved_count = 0
        
        return saved_count
    
    async def get_crawling_status(self, db: Session = None) -> Dict[str, Any]:
        """크롤링 상태 조회"""
        if db is None:
            db = next(get_db())
            should_close_db = True
        else:
            should_close_db = False
        
        try:
            # 최근 24시간 크롤링 작업 조회
            since = datetime.now() - timedelta(hours=24)
            
            recent_jobs = db.query(CrawlingJob).filter(
                CrawlingJob.start_time >= since
            ).all()
            
            # 통계 계산
            total_jobs = len(recent_jobs)
            completed_jobs = len([job for job in recent_jobs if job.status == "completed"])
            failed_jobs = len([job for job in recent_jobs if job.status == "failed"])
            running_jobs = len([job for job in recent_jobs if job.status == "running"])
            
            total_articles = sum(job.articles_saved or 0 for job in recent_jobs)
            
            # 소스별 통계
            source_stats = {}
            for source in NewsSource:
                source_jobs = [job for job in recent_jobs if job.source == source]
                source_stats[source.value] = {
                    "total_jobs": len(source_jobs),
                    "completed": len([job for job in source_jobs if job.status == "completed"]),
                    "failed": len([job for job in source_jobs if job.status == "failed"]),
                    "articles": sum(job.articles_saved or 0 for job in source_jobs)
                }
            
            return {
                "period": "최근 24시간",
                "summary": {
                    "total_jobs": total_jobs,
                    "completed_jobs": completed_jobs,
                    "failed_jobs": failed_jobs,
                    "running_jobs": running_jobs,
                    "success_rate": (completed_jobs / total_jobs * 100) if total_jobs > 0 else 0,
                    "total_articles": total_articles
                },
                "source_stats": source_stats,
                "last_updated": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"크롤링 상태 조회 오류: {e}")
            return {
                "error": str(e),
                "last_updated": datetime.now().isoformat()
            }
        finally:
            if should_close_db:
                db.close()
    
    async def cleanup_old_jobs(self, days_to_keep: int = 30, db: Session = None) -> int:
        """오래된 크롤링 작업 로그 정리"""
        if db is None:
            db = next(get_db())
            should_close_db = True
        else:
            should_close_db = False
        
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)
            
            deleted_count = db.query(CrawlingJob).filter(
                CrawlingJob.start_time < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info(f"오래된 크롤링 작업 로그 정리: {deleted_count}개 삭제")
            return deleted_count
            
        except Exception as e:
            logger.error(f"크롤링 작업 로그 정리 오류: {e}")
            db.rollback()
            return 0
        finally:
            if should_close_db:
                db.close()


# 전역 크롤링 매니저 인스턴스
crawling_manager = CrawlingManager()


def get_crawling_manager() -> CrawlingManager:
    """크롤링 매니저 의존성 주입"""
    return crawling_manager