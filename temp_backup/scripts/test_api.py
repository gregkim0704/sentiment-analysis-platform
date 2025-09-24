#!/usr/bin/env python3
"""
API 테스트 스크립트
"""

import sys
import os
import asyncio
import httpx
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.config import settings

# API 기본 URL
BASE_URL = f"http://{settings.API_HOST}:{settings.API_PORT}"
API_URL = f"{BASE_URL}{settings.API_V1_STR}"

async def test_health_check():
    """헬스체크 테스트"""
    print("🔍 헬스체크 테스트 중...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/health")
            if response.status_code == 200:
                data = response.json()
                print("✅ 헬스체크 성공")
                print(f"   - 상태: {data.get('status')}")
                print(f"   - 버전: {data.get('version')}")
                print(f"   - 환경: {data.get('environment')}")
                return True
            else:
                print(f"❌ 헬스체크 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 헬스체크 오류: {e}")
            return False

async def test_root_endpoint():
    """루트 엔드포인트 테스트"""
    print("🔍 루트 엔드포인트 테스트 중...")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(BASE_URL)
            if response.status_code == 200:
                data = response.json()
                print("✅ 루트 엔드포인트 성공")
                print(f"   - 메시지: {data.get('message')}")
                return True
            else:
                print(f"❌ 루트 엔드포인트 실패: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ 루트 엔드포인트 오류: {e}")
            return False

async def test_register_and_login():
    """회원가입 및 로그인 테스트"""
    print("🔍 회원가입 및 로그인 테스트 중...")
    
    # 테스트 사용자 데이터
    test_user = {
        "email": "test@example.com",
        "password": "TestPassword123",
        "full_name": "테스트 사용자"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # 회원가입 테스트
            register_response = await client.post(
                f"{API_URL}/auth/register",
                json=test_user
            )
            
            if register_response.status_code == 200:
                print("✅ 회원가입 성공")
            elif register_response.status_code == 400:
                print("ℹ️  이미 등록된 사용자 (정상)")
            else:
                print(f"❌ 회원가입 실패: {register_response.status_code}")
                print(f"   응답: {register_response.text}")
                return False
            
            # 로그인 테스트
            login_data = {
                "email": test_user["email"],
                "password": test_user["password"]
            }
            
            login_response = await client.post(
                f"{API_URL}/auth/login",
                json=login_data
            )
            
            if login_response.status_code == 200:
                data = login_response.json()
                print("✅ 로그인 성공")
                print(f"   - 사용자: {data.get('user', {}).get('full_name')}")
                print(f"   - 토큰 타입: {data.get('token_type')}")
                return data.get('access_token')
            else:
                print(f"❌ 로그인 실패: {login_response.status_code}")
                print(f"   응답: {login_response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 회원가입/로그인 오류: {e}")
            return False

async def test_protected_endpoint(access_token):
    """보호된 엔드포인트 테스트"""
    print("🔍 보호된 엔드포인트 테스트 중...")
    
    headers = {"Authorization": f"Bearer {access_token}"}
    
    async with httpx.AsyncClient() as client:
        try:
            # 내 정보 조회
            response = await client.get(
                f"{API_URL}/auth/me",
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 보호된 엔드포인트 접근 성공")
                print(f"   - 사용자: {data.get('full_name')}")
                print(f"   - 이메일: {data.get('email')}")
                print(f"   - 역할: {data.get('role')}")
                return True
            else:
                print(f"❌ 보호된 엔드포인트 접근 실패: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 보호된 엔드포인트 오류: {e}")
            return False

async def test_api_docs():
    """API 문서 접근 테스트"""
    print("🔍 API 문서 접근 테스트 중...")
    
    async with httpx.AsyncClient() as client:
        try:
            # Swagger UI 테스트
            docs_response = await client.get(f"{BASE_URL}/docs")
            if docs_response.status_code == 200:
                print("✅ Swagger UI 접근 성공")
            else:
                print(f"❌ Swagger UI 접근 실패: {docs_response.status_code}")
            
            # OpenAPI 스키마 테스트
            openapi_response = await client.get(f"{API_URL}/openapi.json")
            if openapi_response.status_code == 200:
                print("✅ OpenAPI 스키마 접근 성공")
                return True
            else:
                print(f"❌ OpenAPI 스키마 접근 실패: {openapi_response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ API 문서 접근 오류: {e}")
            return False

async def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("멀티 스테이크홀더 센티멘트 분석 플랫폼 API 테스트")
    print("=" * 60)
    print(f"테스트 대상: {BASE_URL}")
    print()
    
    tests = [
        ("헬스체크", test_health_check),
        ("루트 엔드포인트", test_root_endpoint),
        ("API 문서", test_api_docs),
    ]
    
    passed = 0
    total = len(tests)
    
    # 기본 테스트 실행
    for test_name, test_func in tests:
        print(f"📋 {test_name} 테스트 실행 중...")
        if await test_func():
            passed += 1
        print()
    
    # 인증 관련 테스트
    print("📋 인증 테스트 실행 중...")
    access_token = await test_register_and_login()
    if access_token:
        passed += 1
        print()
        
        print("📋 보호된 엔드포인트 테스트 실행 중...")
        if await test_protected_endpoint(access_token):
            passed += 1
        total += 1
    total += 1
    
    print("=" * 60)
    print(f"테스트 결과: {passed}/{total} 통과")
    
    if passed == total:
        print("🎉 모든 API 테스트가 성공적으로 완료되었습니다!")
        return 0
    else:
        print("⚠️  일부 API 테스트가 실패했습니다.")
        print("💡 서버가 실행 중인지 확인해주세요:")
        print(f"   uvicorn main:app --host {settings.API_HOST} --port {settings.API_PORT}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)