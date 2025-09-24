"""
간단한 테스트용 백엔드 서버
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="센티멘트 분석 플랫폼 - 테스트 서버")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "센티멘트 분석 플랫폼 테스트 서버", "status": "running"}

@app.get("/api/v1/companies")
async def get_companies():
    """회사 목록 반환"""
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
        },
        {
            "id": 3,
            "name": "LG전자",
            "stock_code": "066570",
            "industry": "전자",
            "description": "생활가전 및 전자제품 제조",
            "website_url": "https://www.lge.co.kr",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": None
        }
    ]

@app.get("/api/v1/dashboard")
async def get_dashboard_data():
    """대시보드 데이터 반환"""
    return {
        "overallSentiment": 0.3,
        "totalArticles": 1250,
        "todayArticles": 45,
        "activeStakeholders": 6,
        "activeAlerts": 3,
        "trendData": [
            {"date": "2024-09-18", "overall": 0.1, "customer": 0.0, "investor": 0.2, "employee": -0.1, "media": -0.2},
            {"date": "2024-09-19", "overall": 0.2, "customer": 0.1, "investor": 0.3, "employee": 0.0, "media": -0.1},
            {"date": "2024-09-20", "overall": 0.3, "customer": 0.2, "investor": 0.4, "employee": 0.1, "media": 0.0},
            {"date": "2024-09-21", "overall": 0.1, "customer": 0.0, "investor": 0.2, "employee": -0.1, "media": -0.2},
            {"date": "2024-09-22", "overall": 0.4, "customer": 0.3, "investor": 0.5, "employee": 0.2, "media": 0.1},
            {"date": "2024-09-23", "overall": 0.2, "customer": 0.1, "investor": 0.3, "employee": 0.0, "media": -0.1},
            {"date": "2024-09-24", "overall": 0.3, "customer": 0.2, "investor": 0.4, "employee": 0.1, "media": 0.0}
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

@app.get("/api/v1/companies/{company_id}/news/recent")
async def get_recent_news(company_id: int):
    """최근 뉴스 반환"""
    return [
        {
            "id": 1,
            "title": f"회사 {company_id} - 3분기 실적 발표... 반도체 부문 회복세",
            "url": "https://example.com/news/1",
            "source": "naver",
            "publishedAt": "2024-09-24T10:30:00",
            "sentiment": "positive",
            "sentimentScore": 0.7,
            "stakeholderType": "investor"
        },
        {
            "id": 2,
            "title": f"회사 {company_id} 직원들, 새로운 복지 정책에 긍정적 반응",
            "url": "https://example.com/news/2",
            "source": "daum",
            "publishedAt": "2024-09-24T09:15:00",
            "sentiment": "positive",
            "sentimentScore": 0.5,
            "stakeholderType": "employee"
        },
        {
            "id": 3,
            "title": f"회사 {company_id} 신제품 출시, 소비자들의 관심 집중",
            "url": "https://example.com/news/3",
            "source": "google",
            "publishedAt": "2024-09-24T08:45:00",
            "sentiment": "neutral",
            "sentimentScore": 0.1,
            "stakeholderType": "customer"
        },
        {
            "id": 4,
            "title": f"회사 {company_id} 환경 정책 발표, 지역사회 호응",
            "url": "https://example.com/news/4",
            "source": "naver",
            "publishedAt": "2024-09-24T07:20:00",
            "sentiment": "positive",
            "sentimentScore": 0.6,
            "stakeholderType": "community"
        },
        {
            "id": 5,
            "title": f"회사 {company_id} 주가 하락, 투자자들 우려 표명",
            "url": "https://example.com/news/5",
            "source": "daum",
            "publishedAt": "2024-09-24T06:10:00",
            "sentiment": "negative",
            "sentimentScore": -0.8,
            "stakeholderType": "investor"
        }
    ]

@app.get("/api/v1/companies/{company_id}/alerts")
async def get_alerts(company_id: int):
    """알림 반환"""
    return [
        {
            "id": 1,
            "title": "투자자 센티멘트 급락 감지",
            "message": "최근 24시간 동안 투자자 관련 뉴스의 센티멘트가 -1.2로 급락했습니다.",
            "severity": "warning",
            "createdAt": "2024-09-24T10:00:00",
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
            "createdAt": "2024-09-24T09:30:00",
            "metadata": {
                "stakeholderType": "media",
                "articleCount": 45
            }
        },
        {
            "id": 3,
            "title": "고객 만족도 상승",
            "message": "고객 관련 센티멘트가 지속적으로 상승하고 있습니다.",
            "severity": "info",
            "createdAt": "2024-09-24T08:15:00",
            "metadata": {
                "stakeholderType": "customer",
                "sentimentScore": 0.8,
                "articleCount": 28
            }
        }
    ]

@app.patch("/api/v1/alerts/{alert_id}/dismiss")
async def dismiss_alert(alert_id: int):
    """알림 해제"""
    return {"message": "알림이 해제되었습니다.", "alert_id": alert_id}

@app.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "timestamp": "2024-09-24T20:45:00",
        "version": "1.0.0",
        "environment": "development"
    }

if __name__ == "__main__":
    print("🚀 테스트 서버 시작 중...")
    print("📊 대시보드: http://localhost:8000")
    print("📖 API 문서: http://localhost:8000/docs")
    
    uvicorn.run(
        "simple_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )