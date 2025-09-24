"""
알림 관련 Celery 작업들 (향후 구현)
"""

from app.tasks.celery_app import celery_app
from app.core.logging import logger


@celery_app.task(name="app.tasks.notification_tasks.check_alert_rules_task")
def check_alert_rules_task():
    """알림 규칙 확인 및 알림 발송 (구현 예정)"""
    logger.info("알림 확인 작업 - 구현 예정")
    return {"message": "알림 확인 작업 - 구현 예정"}