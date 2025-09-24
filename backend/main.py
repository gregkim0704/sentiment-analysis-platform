from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from pathlib import Path

app = FastAPI(title="Sentiment Analysis Platform")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 프로덕션에서는 특정 도메인으로 제한
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 정적 파일 서빙 (프론트엔드)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

# API 라우트들
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "API is running"}

@app.get("/api/sentiment")
async def analyze_sentiment():
    # 실제 센티멘트 분석 로직 구현
    return {"sentiment": "positive", "confidence": 0.85}

# 프론트엔드 라우팅 (SPA)
@app.get("/{full_path:path}")
async def serve_frontend(full_path: str):
    """모든 경로를 React 앱으로 라우팅"""
    # API 경로는 제외
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # 정적 파일 경로 확인
    static_file_path = static_dir / full_path
    if static_file_path.is_file():
        return FileResponse(static_file_path)
    
    # SPA 라우팅을 위해 index.html 반환
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    
    raise HTTPException(status_code=404, detail="File not found")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)