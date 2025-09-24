"""
분석 관련 Celery 작업들
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any

from app.tasks.celery_app import celery_app
from app.ml.analysis_manager import get_analysis_manager
from app.core.logging import logger


@celery_app.task(bind=True, name="app.tasks.analysis_tasks.analyze_pending_articles_task")
def analyze_pending_articles_task(self, limit: int = 100) -> Dict[str, Any]:
    """
    센티멘트 분석이 필요한 기사들 처리
    
    Args:
        limit: 처리할 최대 기사 수
    
    Returns:
        분석 결과 딕셔너리
    """
    try:
        logger.info(f"Celery 작업 시작: 센티멘트 분석 (최대 {limit}개)")
        
        # 작업 상태 업데이트
        self.update_state(
            state="PROGRESS",
            meta={"status": "센티멘트 분석 시작", "progress": 0}
        )
        
        # 분석 매니저로 작업 실행
        manager = get_analysis_manager()
        
        # 분석기 초기화 확인
        if not manager.analyzer.is_loaded:
            logger.info("분석기 초기화 중...")
            init_success = asyncio.run(manager.initialize())
            if not init_success:
                raise Exception("분석기 초기화 실패")
        
        # 분석 실행
        result = asyncio.run(manager.analyze_pending_articles(limit))
        
        # 작업 완료 상태 업데이트
        if result.get("success"):
            logger.info(f"센티멘트 분석 완료: {result.get('processed_count', 0)}개 처리")
            self.update_state(
                state="SUCCESS",
                meta={
                    "status": "분석 완료",
                    "progress": 100,
                    "result": result
                }
            )
        else:
            logger.error(f"센티멘트 분석 실패: {result.get('error', 'Unknown error')}")
            self.update_state(
                state="FAILURE",
                meta={
                    "status": "분석 실패",
                    "error": result.get("error", "Unknown error")
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Celery 센티멘트 분석 작업 오류: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": "작업 오류",
                "error": str(e)
            }
        )
        raise


@celery_app.task(bind=True, name="app.tasks.analysis_tasks.aggregate_daily_trends_task")
def aggregate_daily_trends_task(self, target_date: str = None) -> Dict[str, Any]:
    """
    일별 센티멘트 트렌드 집계
    
    Args:
        target_date: 집계할 날짜 (YYYY-MM-DD 형식, None이면 어제)
    
    Returns:
        집계 결과 딕셔너리
    """
    try:
        # 대상 날짜 설정
        if target_date:
            target_datetime = datetime.strptime(target_date, "%Y-%m-%d")
        else:
            # 기본값: 어제
            target_datetime = datetime.now() - timedelta(days=1)
        
        logger.info(f"Celery 작업 시작: 일별 트렌드 집계 ({target_datetime.date()})")
        
        # 작업 상태 업데이트
        self.update_state(
            state="PROGRESS",
            meta={
                "status": f"{target_datetime.date()} 트렌드 집계 시작",
                "progress": 0
            }
        )
        
        # 분석 매니저로 작업 실행
        manager = get_analysis_manager()
        result = asyncio.run(manager.aggregate_daily_trends(target_datetime))
        
        # 작업 완료 상태 업데이트
        if result.get("success"):
            logger.info(f"트렌드 집계 완료: {result.get('aggregated_trends', 0)}개 트렌드")
            self.update_state(
                state="SUCCESS",
                meta={
                    "status": "집계 완료",
                    "progress": 100,
                    "result": result
                }
            )
        else:
            logger.error(f"트렌드 집계 실패: {result.get('error', 'Unknown error')}")
            self.update_state(
                state="FAILURE",
                meta={
                    "status": "집계 실패",
                    "error": result.get("error", "Unknown error")
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Celery 트렌드 집계 작업 오류: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": "작업 오류",
                "error": str(e)
            }
        )
        raise


@celery_app.task(bind=True, name="app.tasks.analysis_tasks.analyze_single_article_task")
def analyze_single_article_task(self, article_id: int) -> Dict[str, Any]:
    """
    단일 기사 센티멘트 분석
    
    Args:
        article_id: 분석할 기사 ID
    
    Returns:
        분석 결과 딕셔너리
    """
    try:
        logger.info(f"Celery 작업 시작: 단일 기사 분석 (ID: {article_id})")
        
        # 작업 상태 업데이트
        self.update_state(
            state="PROGRESS",
            meta={
                "status": f"기사 {article_id} 분석 시작",
                "progress": 50
            }
        )
        
        # 분석 매니저로 작업 실행
        manager = get_analysis_manager()
        
        # 분석기 초기화 확인
        if not manager.analyzer.is_loaded:
            logger.info("분석기 초기화 중...")
            init_success = asyncio.run(manager.initialize())
            if not init_success:
                raise Exception("분석기 초기화 실패")
        
        # 분석 실행
        result = asyncio.run(manager.analyze_single_article(article_id))
        
        # 작업 완료 상태 업데이트
        if result.get("success"):
            logger.info(f"단일 기사 분석 완료 (ID: {article_id})")
            self.update_state(
                state="SUCCESS",
                meta={
                    "status": "분석 완료",
                    "progress": 100,
                    "result": result
                }
            )
        else:
            logger.error(f"단일 기사 분석 실패 (ID: {article_id}): {result.get('error')}")
            self.update_state(
                state="FAILURE",
                meta={
                    "status": "분석 실패",
                    "error": result.get("error")
                }
            )
        
        return result
        
    except Exception as e:
        logger.error(f"Celery 단일 기사 분석 작업 오류: {e}")
        self.update_state(
            state="FAILURE",
            meta={
                "status": "작업 오류",
                "error": str(e)
            }
        )
        raise


@celery_app.task(name="app.tasks.analysis_tasks.get_analysis_statistics_task")
def get_analysis_statistics_task(days: int = 30) -> Dict[str, Any]:
    """
    분석 통계 조회
    
    Args:
        days: 조회할 기간 (일)
    
    Returns:
        통계 데이터 딕셔너리
    """
    try:
        logger.info(f"Celery 작업 시작: 분석 통계 조회 (최근 {days}일)")
        
        # 분석 매니저로 작업 실행
        manager = get_analysis_manager()
        result = asyncio.run(manager.get_analysis_statistics(days))
        
        logger.info("분석 통계 조회 완료")
        return result
        
    except Exception as e:
        logger.error(f"Celery 분석 통계 조회 작업 오류: {e}")
        return {
            "error": str(e),
            "days": days
        }


@celery_app.task(bind=True, name="app.tasks.analysis_tasks.test_analysis_task")
def test_analysis_task(self, test_text: str = "삼성전자의 새로운 제품이 출시되었습니다.") -> Dict[str, Any]:
    """
    센티멘트 분석 테스트 작업
    
    Args:
        test_text: 테스트할 텍스트
    
    Returns:
        테스트 결과 딕셔너리
    """
    try:
        logger.info(f"Celery 테스트 작업 시작: 센티멘트 분석")
        
        # 작업 상태 업데이트
        self.update_state(
            state="PROGRESS",
            meta={
                "status": "분석 테스트 시작",
                "progress": 50
            }
        )
        
        # 분석 매니저 초기화
        manager = get_analysis_manager()
        
        if not manager.analyzer.is_loaded:
            logger.info("분석기 초기화 중...")
            init_success = asyncio.run(manager.initialize())
            if not init_success:
                return {
                    "success": False,
                    "error": "분석기 초기화 실패",
                    "test_mode": True
                }
        
        # 테스트 입력 생성
        from app.ml.base_analyzer import AnalysisInput
        
        test_input = AnalysisInput(
            title="테스트 제목",
            content=test_text,
            company_name="삼성전자",
            author="테스트 작성자",
            source="test"
        )
        
        # 분석 실행
        sentiment_result = asyncio.run(manager.analyzer.analyze_sentiment(test_input))
        stakeholder_result = asyncio.run(manager.analyzer.classify_stakeholder(test_input))
        
        result = {
            "success": True,
            "test_text": test_text,
            "sentiment_result": sentiment_result.to_dict(),
            "stakeholder_result": stakeholder_result.to_dict(),
            "test_mode": True
        }
        
        logger.info("센티멘트 분석 테스트 완료")
        
        self.update_state(
            state="SUCCESS",
            meta={
                "status": "테스트 완료",
                "progress": 100,
                "result": result
            }
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Celery 분석 테스트 작업 오류: {e}")
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