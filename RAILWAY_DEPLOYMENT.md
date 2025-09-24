# Railway 배포 가이드 (추천)

Railway는 가장 경제적이고 간단한 풀스택 배포 옵션입니다.

## 🚀 Railway 배포 단계

### 1단계: Railway 계정 생성
1. [railway.app](https://railway.app) 방문
2. GitHub 계정으로 로그인
3. 월 $5 무료 크레딧 받기

### 2단계: 프로젝트 배포
1. "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. 이 저장소 선택
4. 자동으로 Dockerfile 감지하여 빌드

### 3단계: 데이터베이스 추가 (선택사항)
1. 프로젝트에서 "New" 클릭
2. "Database" > "PostgreSQL" 선택
3. 자동으로 DATABASE_URL 환경변수 생성

### 4단계: 환경 변수 설정
```
NODE_ENV=production
DATABASE_URL=postgresql://... (자동 생성됨)
```

### 5단계: 도메인 확인
- Railway에서 자동으로 도메인 생성
- 커스텀 도메인 연결 가능

## 💰 비용 예상

**무료 크레딧 ($5/월)으로 가능한 사용량:**
- 소규모 앱: 약 500시간 실행 (24/7 운영 시 약 20일)
- 트래픽이 적으면 한 달 내내 무료 운영 가능
- 초과 시 사용량만큼 과금

**실제 비용 (크레딧 소진 후):**
- 기본 서비스: ~$3-5/월
- PostgreSQL: ~$2-3/월
- 총 예상 비용: $5-8/월

## 🔧 배포 후 설정

### 프론트엔드 API URL 수정
Railway 도메인을 확인한 후 프론트엔드 설정 업데이트:

```typescript
// frontend/src/config/api.ts
export const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'https://your-railway-domain.railway.app',
  // ...
};
```

### 자동 배포 설정
- GitHub에 푸시하면 자동으로 재배포
- 브랜치별 배포 환경 설정 가능

## 🆚 다른 옵션과 비교

| 플랫폼 | 무료 티어 | 월 비용 | 장점 | 단점 |
|--------|-----------|---------|------|------|
| Railway | $5 크레딧 | $5-8 | 가장 간단, 통합 관리 | 크레딧 제한 |
| Render | 750시간 | $7-10 | 안정적, 무료 시간 많음 | Sleep 모드 |
| Fly.io | 3앱 무료 | $3-6 | 글로벌 배포, 빠름 | 설정 복잡 |
| Heroku | 없음 | $14+ | 많은 문서 | 비쌈 |

## 🎯 추천 이유

1. **설정 간단**: Dockerfile만 있으면 바로 배포
2. **통합 관리**: 프론트엔드 + 백엔드 + DB 한 곳에서
3. **경제적**: 소규모 앱은 거의 무료
4. **자동 배포**: GitHub 연동으로 CI/CD 자동화
5. **확장성**: 트래픽 증가 시 자동 스케일링

Railway로 시작해서 트래픽이 늘어나면 다른 플랫폼으로 이전하는 것을 추천합니다!