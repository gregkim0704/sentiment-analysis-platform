# GitHub Personal Access Token 생성 가이드

## 🔐 Personal Access Token이 필요한 이유

GitHub는 2021년부터 보안상의 이유로 비밀번호 대신 토큰을 사용하도록 변경했습니다.
- 기존: 사용자명 + 비밀번호
- 현재: 사용자명 + Personal Access Token

## 📋 단계별 토큰 생성 방법

### 1단계: GitHub 로그인 및 설정 페이지 이동

1. **GitHub 웹사이트 접속**
   - 브라우저에서 [github.com](https://github.com) 접속
   - 본인 계정으로 로그인

2. **프로필 메뉴 클릭**
   - 우측 상단 프로필 사진 클릭
   - 드롭다운 메뉴에서 **"Settings"** 클릭

### 2단계: Developer Settings 접근

3. **왼쪽 사이드바에서 Developer settings 찾기**
   - 설정 페이지 왼쪽 사이드바를 아래로 스크롤
   - 맨 아래쪽에 **"Developer settings"** 클릭

4. **Personal access tokens 선택**
   - 왼쪽 메뉴에서 **"Personal access tokens"** 클릭
   - **"Tokens (classic)"** 선택 (Fine-grained tokens 말고)

### 3단계: 새 토큰 생성

5. **Generate new token 버튼 클릭**
   - 페이지 상단의 **"Generate new token"** 버튼 클릭
   - **"Generate new token (classic)"** 선택

6. **토큰 정보 입력**
   ```
   Note (토큰 이름): sentiment-analysis-platform-deploy
   Expiration (만료일): 90 days (또는 No expiration)
   ```

### 4단계: 권한 설정 (매우 중요!)

7. **repo 권한 체크**
   - **"repo"** 체크박스를 클릭 ✅
   - 이렇게 하면 하위 항목들이 자동으로 체크됩니다:
     - ✅ repo:status
     - ✅ repo_deployment
     - ✅ public_repo
     - ✅ repo:invite
     - ✅ security_events

8. **추가 권한 (선택사항)**
   - **"workflow"** ✅ (GitHub Actions 사용 시)
   - **"write:packages"** ✅ (패키지 배포 시)

### 5단계: 토큰 생성 및 복사

9. **토큰 생성**
   - 페이지 하단의 **"Generate token"** 버튼 클릭

10. **토큰 복사 및 저장**
    - 생성된 토큰이 화면에 표시됩니다
    - **⚠️ 중요: 이 토큰은 한 번만 표시됩니다!**
    - **"Copy"** 버튼을 클릭하여 복사
    - 메모장이나 안전한 곳에 저장

## 🔑 토큰 사용 방법

### Git 명령어에서 토큰 사용

```bash
# GitHub 저장소와 연결
git remote add origin https://github.com/YOUR_USERNAME/sentiment-analysis-platform.git

# 브랜치를 main으로 설정
git branch -M main

# GitHub에 업로드 (여기서 토큰 입력)
git push -u origin main
```

### 인증 정보 입력 시:
```
Username for 'https://github.com': YOUR_GITHUB_USERNAME
Password for 'https://YOUR_GITHUB_USERNAME@github.com': 여기에_토큰_붙여넣기
```

## 💡 토큰 관리 팁

### 토큰 저장 (선택사항)
Git이 토큰을 기억하도록 설정:
```bash
# Windows에서 자격 증명 저장
git config --global credential.helper manager-core

# 또는 캐시에 15분간 저장
git config --global credential.helper cache
```

### 토큰 보안 수칙
- ✅ 토큰을 안전한 곳에 저장
- ✅ 정기적으로 토큰 갱신
- ❌ 토큰을 코드에 하드코딩하지 않기
- ❌ 토큰을 공개 저장소에 업로드하지 않기

## 🚨 문제 해결

### "Authentication failed" 오류 시:
1. 토큰이 올바르게 복사되었는지 확인
2. repo 권한이 체크되어 있는지 확인
3. 토큰이 만료되지 않았는지 확인

### 토큰을 잃어버린 경우:
1. GitHub Settings → Developer settings로 이동
2. 기존 토큰 삭제
3. 새 토큰 생성

## ✅ 다음 단계

토큰 생성이 완료되면:
1. 토큰을 안전한 곳에 저장
2. Git 명령어로 GitHub에 코드 업로드
3. Railway 등에서 저장소 연결하여 배포