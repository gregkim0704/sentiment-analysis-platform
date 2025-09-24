"""
Celery 애플리케이션 설정
"""

from celery import Celery
from celery.schedules import crontab
from app.core.config import settings

# Celery 앱 생성
celery_app = Celery(
    "sentiment_analysis",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.crawling_tasks",
        "app.tasks.analysis_tasks",
        "app.tasks.notification_tasks"
    ]
)

# Celery 설정
celery_app.conf.update(
    # 시간대 설정
    timezone=settings.TIMEZONE,
    enable_utc=True,
    
    # 작업 설정
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    
    # 결과 백엔드 설정
    result_expires=3600,  # 1시간 후 결과 만료
    
    # 워커 설정
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    
    # 라우팅 설정
    task_routes={
        "app.tasks.crawling_tasks.*": {"queue": "crawling"},
        "app.tasks.analysis_tasks.*": {"queue": "analysis"},
        "app.tasks.notification_tasks.*": {"queue": "notifications"},
    },
    
    # 스케줄 설정
    beat_schedule={
        # 정기 뉴스 크롤링 (6시간마다)
        "crawl-news-regularly": {
            "task": "app.tasks.crawling_tasks.crawl_all_companies_task",
            "schedule": crontab(minute=0, hour="*/6"),  # 매 6시간마다
            "kwargs": {"days_back": 1}  # 최근 1일 뉴스만
        },
        
        # 전체 뉴스 크롤링 (매일 새벽 2시)
        "crawl-news-daily": {
            "task": "app.tasks.crawling_tasks.crawl_all_companies_task",
            "schedule": crontab(minute=0, hour=2),  # 매일 새벽 2시
            "kwargs": {"days_back": 7}  # 최근 7일 뉴스
        },
        
        # 크롤링 로그 정리 (매주 일요일 새벽 3시)
        "cleanup-crawling-logs": {
            "task": "app.tasks.crawling_tasks.cleanup_old_crawling_logs_task",
            "schedule": crontab(minute=0, hour=3, day_of_week=0),  # 매주 일요일
            "kwargs": {"days_to_keep": 30}
        },
        
        # 센티멘트 분석 (매시간)
        "analyze-sentiment": {
            "task": "app.tasks.analysis_tasks.analyze_pending_articles_task",
            "schedule": crontab(minute=0),  # 매시간
        },
        
        # 트렌드 집계 (매일 새벽 4시)
        "aggregate-trends": {
            "task": "app.tasks.analysis_tasks.aggregate_daily_trends_task",
            "schedule": crontab(minute=0, hour=4),  # 매일 새벽 4시
        },
        
        # 알림 확인 (10분마다)
        "check-alerts": {
            "task": "app.tasks.notification_tasks.check_alert_rules_task",
            "schedule": crontab(minute="*/10"),  # 10분마다
        },
    }
)

# 작업 큐별 설정
celery_app.conf.task_default_queue = "default"
celery_app.conf.task_create_missing_queues = True