"""
크롤링 관리 엔드포인트
"""

from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from celery.result import AsyncResult

from app.core.database import get_db
from app.core.security import get_current_user, require_analyst_or_admin, require_admin
from app.core.logging import logger, log_api_call
from app.crawlers.manager import get_crawling_manager
from app.tasks.crawling_tasks import (
    crawl_all_companies_task,
    crawl_company_task,
    test_crawling_task,
    get_crawling_status_task
)
from app.schemas.base import ResponseSchema
from database.models import User, Company

router = APIRouter()


@router.post("/start", summary="전체 뉴스 크롤링 시작")
@log_api_call
async def start_crawling(
    days_back: Optional[int] = 7,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    current_user: User = Depends(require_analyst_or_admin),
    db: Session = Depends(get_db)
):
    """
    모든 회사의 뉴스 크롤링 시작
    
    - **days_back**: 크롤링할 과거 일수 (기본값: 7일)
    """
    try:
        logger.info(f"전체 뉴스 크롤링 시작 요청 (사용자: {current_user.email}, 기간: {days_back}일)")
        
        # Celery 작업 시작
        task = crawl_all_companies_task.delay(days_back=days_back)
        
        logger.info(f"크롤링 작업 시작됨 - Task ID: {task.id}")
        
        return ResponseSchema(
            success=True,
            message="뉴스 크롤링이 시작되었습니다",
            data={
                "task_id": task.id,
                "days_back": days_back,
                "status": "started",
                "message": "백그라운드에서 크롤링이 진행됩니다. 상태는 /crawling/status/{task_id}에서 확인할 수 있습니다."
            }
        )
        
    except Exception as e:
        logger.error(f"크롤링 시작 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"크롤링 시작 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/company/{company_id}", summary="특정 회사 뉴스 크롤링")
@log_api_call
async def crawl_company(
    company_id: int,
    days_back: Optional[int] = 7,
    current_user: User = Depends(require_analyst_or_admin),
    db: Session = Depends(get_db)
):
    """
    특정 회사의 뉴스 크롤링
    
    - **company_id**: 회사 ID
    - **days_back**: 크롤링할 과거 일수 (기본값: 7일)
    """
    try:
        # 회사 존재 확인
        company = db.query(Company).filter(Company.id == company_id).first()
        if not company:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="회사를 찾을 수 없습니다"
            )
        
        if not company.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="비활성화된 회사입니다"
            )
        
        logger.info(f"회사 뉴스 크롤링 시작 요청 (회사: {company.name}, 사용자: {current_user.email})")
        
        # Celery 작업 시작
        task = crawl_company_task.delay(company_id=company_id, days_back=days_back)
        
        logger.info(f"회사 크롤링 작업 시작됨 - Task ID: {task.id}")
        
        return ResponseSchema(
            success=True,
            message=f"{company.name} 뉴스 크롤링이 시작되었습니다",
            data={
                "task_id": task.id,
                "company_id": company_id,
                "company_name": company.name,
                "days_back": days_back,
                "status": "started"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"회사 크롤링 시작 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"크롤링 시작 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/status/{task_id}", summary="크롤링 작업 상태 조회")
@log_api_call
async def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """
    크롤링 작업 상태 조회
    
    - **task_id**: 작업 ID
    """
    try:
        # Celery 작업 결과 조회
        task_result = AsyncResult(task_id)
        
        if task_result.state == "PENDING":
            response = {
                "task_id": task_id,
                "status": "pending",
                "message": "작업이 대기 중입니다"
            }
        elif task_result.state == "PROGRESS":
            response = {
                "task_id": task_id,
                "status": "progress",
                "message": "작업이 진행 중입니다",
                "meta": task_result.info
            }
        elif task_result.state == "SUCCESS":
            response = {
                "task_id": task_id,
                "status": "success",
                "message": "작업이 완료되었습니다",
                "result": task_result.result
            }
        elif task_result.state == "FAILURE":
            response = {
                "task_id": task_id,
                "status": "failure",
                "message": "작업이 실패했습니다",
                "error": str(task_result.info)
            }
        else:
            response = {
                "task_id": task_id,
                "status": task_result.state.lower(),
                "message": f"작업 상태: {task_result.state}"
            }
        
        return ResponseSchema(
            success=True,
            message="작업 상태 조회 완료",
            data=response
        )
        
    except Exception as e:
        logger.error(f"작업 상태 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작업 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/status", summary="전체 크롤링 상태 조회")
@log_api_call
async def get_crawling_status(
    current_user: User = Depends(get_current_user)
):
    """
    전체 크롤링 상태 및 통계 조회
    """
    try:
        # Celery 작업으로 상태 조회
        task = get_crawling_status_task.delay()
        status_data = task.get(timeout=10)  # 10초 타임아웃
        
        return ResponseSchema(
            success=True,
            message="크롤링 상태 조회 완료",
            data=status_data
        )
        
    except Exception as e:
        logger.error(f"크롤링 상태 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"크롤링 상태 조회 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/test", summary="크롤링 테스트")
@log_api_call
async def test_crawling(
    company_name: Optional[str] = "삼성전자",
    current_user: User = Depends(require_analyst_or_admin)
):
    """
    크롤링 기능 테스트
    
    - **company_name**: 테스트할 회사명 (기본값: 삼성전자)
    """
    try:
        logger.info(f"크롤링 테스트 시작 (회사: {company_name}, 사용자: {current_user.email})")
        
        # Celery 테스트 작업 시작
        task = test_crawling_task.delay(test_company_name=company_name)
        
        return ResponseSchema(
            success=True,
            message="크롤링 테스트가 시작되었습니다",
            data={
                "task_id": task.id,
                "test_company": company_name,
                "status": "started",
                "message": "테스트 결과는 /crawling/status/{task_id}에서 확인할 수 있습니다."
            }
        )
        
    except Exception as e:
        logger.error(f"크롤링 테스트 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"크롤링 테스트 중 오류가 발생했습니다: {str(e)}"
        )


@router.delete("/stop/{task_id}", summary="크롤링 작업 중단")
@log_api_call
async def stop_crawling_task(
    task_id: str,
    current_user: User = Depends(require_admin)
):
    """
    진행 중인 크롤링 작업 중단 (관리자 권한 필요)
    
    - **task_id**: 중단할 작업 ID
    """
    try:
        from app.tasks.celery_app import celery_app
        
        # 작업 취소
        celery_app.control.revoke(task_id, terminate=True)
        
        logger.info(f"크롤링 작업 중단 요청 (Task ID: {task_id}, 사용자: {current_user.email})")
        
        return ResponseSchema(
            success=True,
            message="크롤링 작업 중단 요청이 전송되었습니다",
            data={
                "task_id": task_id,
                "status": "revoked"
            }
        )
        
    except Exception as e:
        logger.error(f"크롤링 작업 중단 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"작업 중단 중 오류가 발생했습니다: {str(e)}"
        )


@router.get("/sources", summary="지원하는 뉴스 소스 목록")
@log_api_call
async def get_news_sources(
    current_user: User = Depends(get_current_user)
):
    """
    지원하는 뉴스 소스 목록 조회
    """
    from database.models import NewsSource
    
    sources = [
        {
            "name": source.value,
            "display_name": {
                "naver": "네이버 뉴스",
                "daum": "다음 뉴스", 
                "google": "구글 뉴스",
                "company_website": "기업 웹사이트",
                "social_media": "소셜 미디어",
                "press_release": "보도자료"
            }.get(source.value, source.value),
            "status": "active"
        }
        for source in NewsSource
    ]
    
    return ResponseSchema(
        success=True,
        message="뉴스 소스 목록 조회 완료",
        data={
            "sources": sources,
            "total_sources": len(sources)
        }
    )


@router.get("/companies", summary="크롤링 대상 회사 목록")
@log_api_call
async def get_crawling_companies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    크롤링 대상 회사 목록 조회
    """
    try:
        companies = db.query(Company).filter(Company.is_active == True).all()
        
        company_list = [
            {
                "id": company.id,
                "name": company.name,
                "stock_code": company.stock_code,
                "industry": company.industry,
                "is_active": company.is_active
            }
            for company in companies
        ]
        
        return ResponseSchema(
            success=True,
            message="크롤링 대상 회사 목록 조회 완료",
            data={
                "companies": company_list,
                "total_companies": len(company_list)
            }
        )
        
    except Exception as e:
        logger.error(f"회사 목록 조회 오류: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"회사 목록 조회 중 오류가 발생했습니다: {str(e)}"
        )