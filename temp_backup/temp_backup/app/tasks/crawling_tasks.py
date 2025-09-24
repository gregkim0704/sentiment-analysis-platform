"""
크롤링 관련 Celery 작업들
"""

from celery import current_task
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional

from app.tasks.celery_app import celery_app
from app.crawlers.manager import get_crawling_manager
from app.core.database import get_db
from app.core.logging import logger
from database.models import Company


@celery_app.task(bind=True, name="app.tasks.crawling_tasks.crawl_all_companies_task")
def crawl_all_companies_task(self, days_back: int = 7) -> Dict[str, Any]:
    """
    모든 회사의 뉴스 크롤링 작업
    
    Args:
        days_back: 크롤링할 과거 일수
    
    Returns:
        크롤링 결과 딕셔너리
    """
    try:
        logger.info(f"Celery 작업 시작: 전체 회사 뉴스 크롤링 (최근 {days_back}일)")
        
        # 작업 상태 업데이트
        self.update_state(
            state="PROGRESS",
            meta={"status": "크롤링 시작", "progress": 0}
        )
        
        # 크롤링 매니저로 작업 실행
        import asyncio
        manager = get_crawling_manager()
        result = asyncio.run(manager.crawl_all_companies(days_back))
        
        # 작업 완료 상태 업데이트
        if result.get("success"):
            logger.info(f"Celery 작업 완료: {result.get('total_articles', 0)}개 기사 수집")
            self.update_state(
                state="SUCCESS",
                meta={
                    "status": "크롤링 완료",
                    "progress": 100,
                    "result": result
                }
            )
        else:
            logger.error(f"Celery 작업 실패: {result.get('error', 'Unknown error')}")
            self.update_state(
                state="FAILURE",
                meta={
                    "status": "크롤링 실패",
                    "error": result.get("error", "Unknown error")
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Celery 크롤링 작업 오류: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": "작업 오류",
                "error": str(e)
            }
        )
        raise


@celery_app.task(bind=True, name="app.tasks.crawling_tasks.crawl_company_task")
def crawl_company_task(self, company_id: int, days_back: int = 7) -> Dict[str, Any]:
    """
    특정 회사의 뉴스 크롤링 작업
    
    Args:
        company_id: 회사 ID
        days_back: 크롤링할 과거 일수
    
    Returns:
        크롤링 결과 딕셔너리
    """
    try:
        logger.info(f"Celery 작업 시작: 회사 뉴스 크롤링 (ID: {company_id})")
        
        # 회사 정보 조회
        db = next(get_db())
        try:
            company = db.query(Company).filter(Company.id == company_id).first()
            if not company:
                raise ValueError(f"회사를 찾을 수 없습니다: ID {company_id}")
            
            if not company.is_active:
                raise ValueError(f"비활성 회사입니다: {company.name}")
            
            # 작업 상태 업데이트
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": f"{company.name} 크롤링 시작",
                    "progress": 0,
                    "company_name": company.name
                }
            )
            
            # 크롤링 실행
            import asyncio
            manager = get_crawling_manager()
            result = asyncio.run(manager.crawl_company_news(company, days_back, db))
            
            # 작업 완료 상태 업데이트
            if result.get("success"):
                logger.info(f"회사 크롤링 완료 ({company.name}): {result.get('articles_saved', 0)}개 기사")
                self.update_state(
                    state="SUCCESS",
                    meta={
                        "status": "크롤링 완료",
                        "progress": 100,
                        "company_name": company.name,
                        "result": result
                    }
                )
            else:
                logger.error(f"회사 크롤링 실패 ({company.name}): {result.get('error')}")
                self.update_state(
                    state="FAILURE",
                    meta={
                        "status": "크롤링 실패",
                        "company_name": company.name,
                        "error": result.get("error")
                    }
                )
            
            return result
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Celery 회사 크롤링 작업 오류: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": "작업 오류",
                "error": str(e)
            }
        )
        raise


@celery_app.task(name="app.tasks.crawling_tasks.cleanup_old_crawling_logs_task")
def cleanup_old_crawling_logs_task(days_to_keep: int = 30) -> Dict[str, Any]:
    """
    오래된 크롤링 로그 정리 작업
    
    Args:
        days_to_keep: 보관할 일수
    
    Returns:
        정리 결과 딕셔너리
    """
    try:
        logger.info(f"Celery 작업 시작: 크롤링 로그 정리 ({days_to_keep}일 이전)")
        
        import asyncio
        manager = get_crawling_manager()
        deleted_count = asyncio.run(manager.cleanup_old_jobs(days_to_keep))
        
        result = {
            "success": True,
            "deleted_count": deleted_count,
            "days_to_keep": days_to_keep,
            "message": f"{deleted_count}개의 오래된 크롤링 로그를 정리했습니다"
        }
        
        logger.info(f"크롤링 로그 정리 완료: {deleted_count}개 삭제")
        return result
        
    except Exception as e:
        logger.error(f"Celery 로그 정리 작업 오류: {e}")
        return {
            "success": False,
            "error": str(e),
            "deleted_count": 0
        }


@celery_app.task(name="app.tasks.crawling_tasks.get_crawling_status_task")
def get_crawling_status_task() -> Dict[str, Any]:
    """
    크롤링 상태 조회 작업
    
    Returns:
        크롤링 상태 딕셔너리
    """
    try:
        logger.info("Celery 작업 시작: 크롤링 상태 조회")
        
        import asyncio
        manager = get_crawling_manager()
        status = asyncio.run(manager.get_crawling_status())
        
        logger.info("크롤링 상태 조회 완료")
        return status
        
    except Exception as e:
        logger.error(f"Celery 상태 조회 작업 오류: {e}")
        return {
            "error": str(e),
            "last_updated": None
        }


@celery_app.task(bind=True, name="app.tasks.crawling_tasks.test_crawling_task")
def test_crawling_task(self, test_company_name: str = "삼성전자") -> Dict[str, Any]:
    """
    크롤링 테스트 작업
    
    Args:
        test_company_name: 테스트할 회사명
    
    Returns:
        테스트 결과 딕셔너리
    """
    try:
        logger.info(f"Celery 테스트 작업 시작: {test_company_name} 크롤링")
        
        # 테스트 회사 조회
        db = next(get_db())
        try:
            company = db.query(Company).filter(
                Company.name == test_company_name,
                Company.is_active == True
            ).first()
            
            if not company:
                return {
                    "success": False,
                    "error": f"테스트 회사를 찾을 수 없습니다: {test_company_name}",
                    "available_companies": [c.name for c in db.query(Company).filter(Company.is_active == True).limit(5).all()]
                }
            
            # 작업 상태 업데이트
            self.update_state(
                state="PROGRESS",
                meta={
                    "status": f"{company.name} 테스트 크롤링 시작",
                    "progress": 50
                }
            )
            
            # 테스트 크롤링 (최근 1일만)
            import asyncio
            manager = get_crawling_manager()
            result = asyncio.run(manager.crawl_company_news(company, 1, db))
            
            # 결과에 테스트 정보 추가
            result["test_mode"] = True
            result["test_company"] = test_company_name
            
            logger.info(f"크롤링 테스트 완료: {result.get('articles_saved', 0)}개 기사")
            
            self.update_state(
                state="SUCCESS",
                meta={
                    "status": "테스트 완료",
                    "progress": 100,
                    "result": result
                }
            )
            
            return result
            
        finally:
            db.close()
        
    except Exception as e:
        logger.error(f"Celery 테스트 작업 오류: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": "테스트 실패",
                "error": str(e)
            }
        )
        return {
            "success": False,
            "error": str(e),
            "test_mode": True
        }