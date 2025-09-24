# GitHub 저장소 생성 및 업로드 가이드

## 🔄 GitHub에 프로젝트 업로드하기

### 1단계: .gitignore 파일 생성
먼저 불필요한 파일들이 업로드되지 않도록 설정합니다.
### 2단계
: Git 초기화 및 커밋
터미널에서 다음 명령어들을 순서대로 실행하세요:

```bash
# Git 저장소 초기화
git init

# 모든 파일 추가
git add .

# 첫 번째 커밋
git commit -m "Initial commit: Sentiment Analysis Platform"
```

### 3단계: GitHub에서 새 저장소 생성
1. [github.com](https://github.com)에 로그인
2. 우측 상단 "+" 버튼 클릭 → "New repository"
3. Repository name: `sentiment-analysis-platform` (또는 원하는 이름)
4. Description: `멀티 스테이크홀더 센티멘트 분석 플랫폼`
5. Public 또는 Private 선택
6. **"Add a README file" 체크 해제** (이미 로컬에 파일들이 있으므로)
7. "Create repository" 클릭

### 4단계: 로컬 저장소와 GitHub 연결
GitHub에서 생성한 저장소 페이지에 나오는 명령어를 복사해서 실행:

```bash
# GitHub 저장소와 연결 (YOUR_USERNAME을 실제 사용자명으로 변경)
git remote add origin https://github.com/YOUR_USERNAME/sentiment-analysis-platform.git

# 기본 브랜치를 main으로 설정
git branch -M main

# GitHub에 업로드
git push -u origin main
```

### 5단계: 업로드 확인
- GitHub 저장소 페이지에서 파일들이 정상적으로 업로드되었는지 확인
- README.md, frontend/, backend/ 폴더 등이 보여야 함

## 🔐 인증 방법

### 방법 1: Personal Access Token (추천)
1. GitHub Settings → Developer settings → Personal access tokens → Tokens (classic)
2. "Generate new token" 클릭
3. 권한: `repo` 체크
4. 토큰 생성 후 복사
5. Git 명령어 실행 시 비밀번호 대신 토큰 입력

### 방법 2: SSH 키 (고급 사용자)
```bash
# SSH 키 생성
ssh-keygen -t ed25519 -C "your_email@example.com"

# 공개 키를 GitHub에 등록
cat ~/.ssh/id_ed25519.pub
```

## 🚨 주의사항

### 민감한 정보 확인
업로드 전에 다음 파일들에 민감한 정보가 없는지 확인:
- API 키
- 데이터베이스 비밀번호  
- 개인정보

### .env 파일 처리
```bash
# .env 파일이 있다면 .env.example로 복사
cp .env .env.example

# .env.example에서 실제 값들을 플레이스홀더로 변경
# 예: DATABASE_URL=your_database_url_here
```

## ✅ 업로드 완료 후 할 일

1. **README.md 업데이트**: 프로젝트 설명 추가
2. **라이선스 추가**: MIT, Apache 등 선택
3. **이슈 템플릿 생성**: .github/ISSUE_TEMPLATE/
4. **PR 템플릿 생성**: .github/pull_request_template.md

## 🔄 이후 작업 흐름

```bash
# 코드 수정 후
git add .
git commit -m "설명적인 커밋 메시지"
git push

# 새 기능 개발 시
git checkout -b feature/new-feature
# 개발 완료 후
git checkout main
git merge feature/new-feature
git push
```

GitHub 업로드가 완료되면 Railway, Render 등에서 이 저장소를 선택해서 배포할 수 있습니다!