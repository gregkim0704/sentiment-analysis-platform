# 멀티 스테이크홀더 센티멘트 분석 플랫폼

## 프로젝트 개요
다양한 스테이크홀더(고객, 투자자, 직원, 정부, 언론 등)의 센티멘트를 실시간으로 분석하는 플랫폼입니다.

## 주요 기능
- 🔍 **다중 소스 뉴스 크롤링**: 네이버, 다음, 구글 등 다양한 소스에서 뉴스 수집
- 🧠 **AI 센티멘트 분석**: 한국어 특화 BERT 모델을 활용한 정확한 감정 분석
- 👥 **스테이크홀더별 분류**: 고객, 투자자, 직원, 정부, 언론 등 8개 그룹별 분석
- 📊 **실시간 대시보드**: 트렌드 시각화 및 인사이트 제공
- 🚨 **스마트 알림**: 임계값 기반 자동 알림 시스템
- 📈 **고급 분석**: 키워드 분석, 센티멘트 변동성, 예측 모델

## 기술 스택
- **Backend**: FastAPI + Python 3.11
- **Frontend**: React + TypeScript
- **Database**: PostgreSQL 15 + Redis 7
- **AI/ML**: Transformers + PyTorch + KoNLPy
- **Monitoring**: Prometheus + Grafana
- **Deployment**: Docker + Docker Compose
- **Task Queue**: Celery + Flower

## 프로젝트 구조
```
sentiment-analysis-platform/
├── database/                 # 데이터베이스 모델 및 설정
│   ├── models.py            # SQLAlchemy 모델 정의
│   └── database.py          # DB 연결 및 초기화
├── sql/                     # SQL 스크립트
│   └── init.sql            # 데이터베이스 초기화 스크립트
├── scripts/                 # 유틸리티 스크립트
│   ├── init_db.py          # DB 초기화 스크립트
│   └── test_db.py          # DB 테스트 스크립트
├── alembic/                 # 데이터베이스 마이그레이션
├── logs/                    # 로그 파일
├── models/                  # AI 모델 저장소
├── static/                  # 정적 파일
├── docker-compose.yml       # Docker 컨테이너 설정
├── Dockerfile              # Docker 이미지 빌드
├── requirements.txt        # Python 의존성
└── .env.example           # 환경변수 예시
```

## 데이터베이스 스키마

### 핵심 테이블
- **users**: 사용자 관리 (관리자, 분석가, 뷰어)
- **companies**: 분석 대상 회사 정보
- **news_articles**: 수집된 뉴스 기사 및 센티멘트 분석 결과
- **sentiment_trends**: 일별 센티멘트 트렌드 집계
- **analysis_requests**: 사용자 분석 요청 및 결과
- **alert_rules**: 알림 규칙 설정
- **crawling_jobs**: 크롤링 작업 로그

### 스테이크홀더 타입
- 👥 **CUSTOMER**: 고객
- 💰 **INVESTOR**: 투자자  
- 👨‍💼 **EMPLOYEE**: 직원
- 🏛️ **GOVERNMENT**: 정부/규제기관
- 📰 **MEDIA**: 언론
- 🤝 **PARTNER**: 파트너/협력사
- 🏢 **COMPETITOR**: 경쟁사
- 🌍 **COMMUNITY**: 지역사회

## 설치 및 실행

### 1. 환경 설정
```bash
# 저장소 클론
git clone <repository-url>
cd sentiment-analysis-platform

# 환경변수 설정
cp .env.example .env
# .env 파일을 편집하여 실제 값으로 수정
```

### 2. Docker로 실행 (권장)
```bash
# 모든 서비스 시작
docker-compose up -d

# 로그 확인
docker-compose logs -f api
```

### 3. 수동 설치
```bash
# Python 가상환경 생성
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 데이터베이스 초기화
python scripts/init_db.py

# 데이터베이스 테스트
python scripts/test_db.py

# 서버 실행
uvicorn main:app --reload

# Celery 워커 시작 (별도 터미널)
celery -A app.tasks.celery_app worker --loglevel=info

# Celery Beat 스케줄러 시작 (별도 터미널)
celery -A app.tasks.celery_app beat --loglevel=info

# API 테스트
python scripts/test_api.py

# 크롤링 시스템 테스트
python scripts/test_crawling.py

# 센티멘트 분석 시스템 테스트
python scripts/test_sentiment.py

# 스테이크홀더 분석 시스템 테스트
python scripts/test_stakeholders.py
```

## 서비스 접근

### 개발 환경
- **API 서버**: http://localhost:8000
- **API 문서**: http://localhost:8000/docs
- **Grafana**: http://localhost:3000 (admin/admin123)
- **Prometheus**: http://localhost:9090
- **Flower**: http://localhost:5555
- **pgAdmin**: http://localhost:5050 (admin@sentiment-analysis.com/admin123)

### 기본 계정
- **관리자**: admin@sentiment-analysis.com / admin123

## 개발 단계
1. ✅ **데이터베이스 스키마 설계** - 완료
   - SQLAlchemy 모델 정의
   - 초기화 스크립트 작성
   - 성능 최적화 인덱스
   - 테스트 스크립트 구현

2. ✅ **백엔드 API 구현 (FastAPI)** - 완료
   - FastAPI 애플리케이션 구조
   - 사용자 인증/권한 시스템
   - JWT 토큰 기반 인증
   - API 엔드포인트 기본 구조
   - 예외 처리 및 로깅
   - 보안 미들웨어
   - API 문서화 (Swagger/ReDoc)

3. ✅ **뉴스 크롤링 시스템** - 완료
   - 다중 소스 크롤러 (네이버, 다음, 구글)
   - 비동기 크롤링 엔진
   - 크롤링 매니저 및 스케줄러
   - Celery 백그라운드 작업 시스템
   - 크롤링 API 엔드포인트
   - 데이터 정제 및 중복 제거
   - 크롤링 상태 모니터링
4. ✅ **센티멘트 분석 모델** - 완료
   - 한국어 특화 BERT 모델 (KLUE)
   - 키워드 기반 감정 분석
   - 스테이크홀더 자동 분류 (8개 그룹)
   - 배치 분석 시스템
   - 센티멘트 트렌드 집계
   - 분석 API 엔드포인트
   - 신뢰도 점수 및 추론 근거 제공

5. ✅ **스테이크홀더 그룹 확장** - 완료
   - 8개 스테이크홀더 그룹별 특화 분석
   - 고객/투자자/직원 전문 분석기
   - 영향도 및 긴급도 자동 계산
   - 스테이크홀더별 액션 아이템 생성
   - 비교 분석 및 인사이트 제공
   - 특화 키워드 사전 및 분석 로직

6. 🔄 **프론트엔드 개발** - 다음 단계
7. 🔄 **실시간 모니터링**

## 성능 최적화
- PostgreSQL 전문 검색 인덱스 (GIN)
- 복합 인덱스로 쿼리 최적화
- Redis 캐싱으로 응답 속도 향상
- Celery 비동기 작업 처리
- 데이터베이스 파티셔닝 지원

## 모니터링
- Prometheus 메트릭 수집
- Grafana 대시보드
- 애플리케이션 로그
- 데이터베이스 성능 모니터링
- Celery 작업 모니터링

## 라이선스
MIT License