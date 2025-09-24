# GitHub 토큰 생성 - 화면별 상세 가이드

## 🖥️ 실제 화면에서 따라하기

### 1️⃣ GitHub 로그인 후 Settings 이동

**현재 화면**: GitHub 메인 페이지
```
1. 우측 상단 프로필 사진 (동그란 아이콘) 클릭
2. 드롭다운 메뉴가 나타남
3. 메뉴에서 "Settings" 클릭
```

**찾는 메뉴**:
```
📋 Your profile
📊 Your repositories  
📦 Your projects
⭐ Your stars
📝 Your gists
───────────────
⚙️ Settings        ← 이것 클릭!
```

### 2️⃣ Settings 페이지에서 Developer settings 찾기

**현재 화면**: Settings 페이지 (왼쪽에 긴 메뉴 리스트)
```
왼쪽 사이드바를 아래로 스크롤하여 맨 아래 찾기
```

**왼쪽 메뉴 구조**:
```
👤 Public profile
📧 Account
🔐 Account security
📧 Emails
🔔 Notifications
💳 Billing and plans
📧 SSH and GPG keys
🏢 Organizations
📦 Repositories
📦 Packages
📄 Pages
💾 Saved replies
🔗 Applications
📧 Scheduled reminders
───────────────────────
🔧 Developer settings  ← 맨 아래 이것!
```

### 3️⃣ Developer settings에서 Personal access tokens 선택

**현재 화면**: Developer settings 페이지
```
왼쪽에 새로운 메뉴가 나타남
```

**Developer settings 메뉴**:
```
🔧 GitHub Apps
🔑 OAuth Apps  
🎫 Personal access tokens  ← 이것 클릭!
   └── 📋 Tokens (classic)   ← 이것 선택!
   └── 🔐 Fine-grained tokens (사용 안 함)
```

### 4️⃣ 새 토큰 생성 버튼 클릭

**현재 화면**: Personal access tokens (classic) 페이지
```
페이지 상단에 버튼들이 있음
```

**찾는 버튼**:
```
🔄 Regenerate token    📝 Generate new token  ← 이것 클릭!
```

**드롭다운이 나타나면**:
```
📝 Generate new token (classic)  ← 이것 선택!
🔐 Generate new token (beta) (사용 안 함)
```

### 5️⃣ 토큰 정보 입력 화면

**현재 화면**: New personal access token 생성 페이지

**입력할 정보**:
```
📝 Note (토큰 이름):
   sentiment-analysis-platform

📅 Expiration (만료일):
   90 days (또는 No expiration 선택)
```

### 6️⃣ 권한 설정 (가장 중요!)

**현재 화면**: 권한 선택 체크박스들이 길게 나열됨

**반드시 체크할 항목**:
```
✅ repo                    ← 이것만 체크하면 됨!
   ✅ repo:status         (자동 체크됨)
   ✅ repo_deployment     (자동 체크됨)  
   ✅ public_repo         (자동 체크됨)
   ✅ repo:invite         (자동 체크됨)
   ✅ security_events     (자동 체크됨)

⬜ workflow               ← 선택사항 (GitHub Actions 사용 시)
⬜ write:packages        ← 선택사항
⬜ delete_repo           ← 체크 안 함
⬜ notifications         ← 체크 안 함
⬜ user                  ← 체크 안 함
⬜ delete:packages       ← 체크 안 함
⬜ admin:org             ← 체크 안 함
⬜ admin:public_key      ← 체크 안 함
⬜ admin:repo_hook       ← 체크 안 함
⬜ admin:org_hook        ← 체크 안 함
⬜ gist                  ← 체크 안 함
⬜ admin:gpg_key         ← 체크 안 함
```

### 7️⃣ 토큰 생성 및 복사

**현재 화면**: 권한 설정 완료 후
```
페이지 맨 아래 초록색 버튼 클릭
```

**클릭할 버튼**:
```
🟢 Generate token  ← 클릭!
```

**토큰 생성 후 화면**:
```
🎉 Personal access token generated successfully!

ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  📋 Copy

⚠️ Make sure to copy your personal access token now. 
   You won't be able to see it again!
```

**중요한 작업**:
```
1. 📋 Copy 버튼 클릭
2. 메모장에 토큰 저장
3. 토큰 형태: ghp_로 시작하는 40자 문자열
```

## 🔄 토큰 사용하기

### Git 명령어 실행
```bash
# 1. GitHub 저장소 연결
git remote add origin https://github.com/YOUR_USERNAME/sentiment-analysis-platform.git

# 2. 브랜치 설정
git branch -M main

# 3. 업로드 (여기서 토큰 입력!)
git push -u origin main
```

### 인증 정보 입력 예시
```
Username for 'https://github.com': your_github_username
Password for 'https://your_github_username@github.com': ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## ✅ 성공 확인

업로드 성공 시 다음과 같은 메시지가 나타납니다:
```
Enumerating objects: 316, done.
Counting objects: 100% (316/316), done.
Delta compression using up to 8 threads
Compressing objects: 100% (298/298), done.
Writing objects: 100% (316/316), 2.1 MiB | 1.2 MiB/s, done.
Total 316 (delta 45), reused 0 (delta 0), pack-reused 0
remote: Resolving deltas: 100% (45/45), done.
To https://github.com/YOUR_USERNAME/sentiment-analysis-platform.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

이제 GitHub 저장소에 코드가 업로드되어 Railway 등에서 배포할 수 있습니다!