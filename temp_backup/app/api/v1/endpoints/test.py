"""
테스트 엔드포인트 (데이터베이스 없이 동작)
"""

from fastapi import APIRouter
from typing import List

router = APIRouter()

@router.get("/companies", summary="테스트용 회사 목록")
async def get_test_companies():
    """테스트용 회사 목록 반환"""
    return [
        {
            "id": 1,
            "name": "삼성전자",
            "stock_code": "005930",
            "industry": "전자",
            "description": "글로벌 전자 기업",
            "website_url": "https://www.samsung.com",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None
        },
        {
            "id": 2,
            "name": "SK하이닉스",
            "stock_code": "000660",
            "industry": "반도체",
            "description": "메모리 반도체 전문 기업",
            "website_url": "https://www.skhynix.com",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None
        }
    ]

@router.get("/dashboard", summary="테스트용 대시보드 데이터")
async def get_test_dashboard_data():
    """테스트용 대시보드 데이터 반환"""
    return {
        "overallSentiment": 0.3,
        "totalArticles": 1250,
        "todayArticles": 45,
        "activeStakeholders": 6,
        "activeAlerts": 3,
        "trendData": [
            {"date": "2024-01-01", "overall": 0.2, "customer": 0.1, "investor": 0.3, "employee": 0.0, "media": -0.1},
            {"date": "2024-01-02", "overall": 0.3, "customer": 0.2, "investor": 0.4, "employee": 0.1, "media": 0.0},
            {"date": "2024-01-03", "overall": 0.1, "customer": 0.0, "investor": 0.2, "employee": -0.1, "media": -0.2},
            {"date": "2024-01-04", "overall": 0.4, "customer": 0.3, "investor": 0.5, "employee": 0.2, "media": 0.1},
            {"date": "2024-01-05", "overall": 0.2, "customer": 0.1, "investor": 0.3, "employee": 0.0, "media": -0.1}
        ],
        "stakeholderData": [
            {"name": "customer", "value": 320, "sentiment": 0.2},
            {"name": "investor", "value": 280, "sentiment": 0.4},
            {"name": "employee", "value": 150, "sentiment": 0.1},
            {"name": "media", "value": 200, "sentiment": -0.1},
            {"name": "government", "value": 100, "sentiment": 0.0},
            {"name": "partner", "value": 120, "sentiment": 0.3}
        ],
        "sentimentDistribution": [
            {"sentiment": "very_positive", "count": 125, "percentage": 10.0},
            {"sentiment": "positive", "count": 375, "percentage": 30.0},
            {"sentiment": "neutral", "count": 500, "percentage": 40.0},
            {"sentiment": "negative", "count": 200, "percentage": 16.0},
            {"sentiment": "very_negative", "count": 50, "percentage": 4.0}
        ]
    }

@router.get("/companies/{company_id}/news/recent", summary="테스트용 최근 뉴스")
async def get_test_recent_news(company_id: int):
    """테스트용 최근 뉴스 반환"""
    return [
        {
            "id": 1,
            "title": "삼성전자, 3분기 실적 발표... 반도체 부문 회복세",
            "url": "https://example.com/news/1",
            "source": "naver",
            "publishedAt": "2024-01-05T10:30:00",
            "sentiment": "positive",
            "sentimentScore": 0.7,
            "stakeholderType": "investor"
        },
        {
            "id": 2,
            "title": "삼성전자 직원들, 새로운 복지 정책에 긍정적 반응",
            "url": "https://example.com/news/2",
            "source": "daum",
            "publishedAt": "2024-01-05T09:15:00",
            "sentiment": "positive",
            "sentimentScore": 0.5,
            "stakeholderType": "employee"
        },
        {
            "id": 3,
            "title": "삼성전자 신제품 출시, 소비자들의 관심 집중",
            "url": "https://example.com/news/3",
            "source": "google",
            "publishedAt": "2024-01-05T08:45:00",
            "sentiment": "neutral",
            "sentimentScore": 0.1,
            "stakeholderType": "customer"
        }
    ]

@router.get("/companies/{company_id}/alerts", summary="테스트용 알림")
async def get_test_alerts(company_id: int):
    """테스트용 알림 반환"""
    return [
        {
            "id": 1,
            "title": "투자자 센티멘트 급락 감지",
            "message": "최근 24시간 동안 투자자 관련 뉴스의 센티멘트가 -1.2로 급락했습니다.",
            "severity": "warning",
            "createdAt": "2024-01-05T10:00:00",
            "metadata": {
                "stakeholderType": "investor",
                "sentimentScore": -1.2,
                "articleCount": 15
            }
        },
        {
            "id": 2,
            "title": "언론 보도량 급증",
            "message": "언론 관련 기사가 평소보다 300% 증가했습니다.",
            "severity": "info",
            "createdAt": "2024-01-05T09:30:00",
            "metadata": {
                "stakeholderType": "media",
                "articleCount": 45
            }
        }
    ]

@router.patch("/alerts/{alert_id}/dismiss", summary="테스트용 알림 해제")
async def dismiss_test_alert(alert_id: int):
    """테스트용 알림 해제"""
    return {"message": "알림이 해제되었습니다.", "alert_id": alert_id}