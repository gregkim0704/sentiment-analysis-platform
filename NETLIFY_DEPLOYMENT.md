# Netlify 배포 가이드

이 가이드는 React 프론트엔드를 Netlify에 배포하는 방법을 설명합니다.

## 🚀 배포 방법

### 방법 1: Netlify 웹 인터페이스 사용 (추천)

1. **Netlify 계정 생성**
   - [netlify.com](https://netlify.com)에서 계정 생성
   - GitHub 계정으로 로그인 권장

2. **새 사이트 생성**
   - "New site from Git" 클릭
   - GitHub 저장소 연결
   - 이 프로젝트 저장소 선택

3. **빌드 설정**
   - Build command: `cd frontend && npm run build`
   - Publish directory: `frontend/build`
   - Node version: `18` (환경 변수에서 설정)

4. **환경 변수 설정**
   - Site settings > Environment variables
   - `REACT_APP_API_URL`: 백엔드 API URL 입력

### 방법 2: Netlify CLI 사용

```bash
# Netlify CLI 설치
npm install -g netlify-cli

# 로그인
netlify login

# 프로젝트 루트에서 배포
netlify deploy

# 프로덕션 배포
netlify deploy --prod
```

### 방법 3: GitHub Actions 자동 배포

1. **GitHub Secrets 설정**
   - Repository Settings > Secrets and variables > Actions
   - 다음 secrets 추가:
     - `NETLIFY_AUTH_TOKEN`: Netlify Personal Access Token
     - `NETLIFY_SITE_ID`: Netlify Site ID

2. **토큰 생성 방법**
   - Netlify > User settings > Personal access tokens
   - "New access token" 생성

3. **Site ID 확인**
   - Netlify > Site settings > General > Site details

## 📁 생성된 파일들

- `netlify.toml`: Netlify 빌드 설정
- `frontend/.env.production`: 프로덕션 환경 변수
- `frontend/public/_redirects`: SPA 라우팅 설정
- `.github/workflows/netlify-deploy.yml`: GitHub Actions 워크플로우

## ⚙️ 설정 수정 사항

### 1. 백엔드 API URL 변경
`frontend/.env.production` 파일에서 실제 백엔드 URL로 변경:
```
REACT_APP_API_URL=https://your-actual-backend-url.com
```

### 2. netlify.toml에서 API 프록시 설정
```toml
[[redirects]]
  from = "/api/*"
  to = "https://your-backend-url.com/api/:splat"
  status = 200
  force = true
```

## 🔧 백엔드 배포 옵션

Netlify는 정적 사이트 호스팅이므로 FastAPI 백엔드는 별도 배포 필요:

1. **Heroku** (추천)
2. **Railway**
3. **Render**
4. **AWS EC2/ECS**
5. **Google Cloud Run**

## 📝 배포 후 확인사항

- [ ] 사이트가 정상적으로 로드되는지 확인
- [ ] API 호출이 정상적으로 작동하는지 확인
- [ ] 라우팅이 제대로 작동하는지 확인 (새로고침 시에도)
- [ ] 환경 변수가 올바르게 설정되었는지 확인

## 🐛 문제 해결

### 빌드 실패 시
- Node.js 버전 확인 (18 권장)
- 의존성 설치 확인: `cd frontend && npm install`
- 로컬에서 빌드 테스트: `cd frontend && npm run build`

### API 호출 실패 시
- CORS 설정 확인 (백엔드)
- API URL 환경 변수 확인
- 네트워크 탭에서 요청 URL 확인

### 라우팅 문제 시
- `_redirects` 파일 확인
- `netlify.toml`의 리다이렉트 설정 확인

## 📞 지원

배포 중 문제가 발생하면 Netlify 문서를 참조하거나 이슈를 생성해주세요.