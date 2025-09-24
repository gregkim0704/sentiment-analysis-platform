#!/usr/bin/env python3
"""
크롤링 시스템 테스트 스크립트
"""

import sys
import os
import asyncio
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.crawlers.naver_crawler import NaverNewsCrawler
from app.crawlers.daum_crawler import DaumNewsCrawler
from app.crawlers.google_crawler import GoogleNewsCrawler
from app.crawlers.manager import get_crawling_manager
from app.core.database import get_db
from app.core.logging import setup_logging, logger
from database.models import Company


async def test_individual_crawlers():
    """개별 크롤러 테스트"""
    print("🔍 개별 크롤러 테스트 시작...")
    
    # 테스트용 회사 객체 생성
    test_company = Company(
        id=1,
        name="삼성전자",
        stock_code="005930",
        industry="전자/IT",
        is_active=True
    )
    
    crawlers = [
        ("네이버 뉴스", NaverNewsCrawler()),
        ("다음 뉴스", DaumNewsCrawler()),
        ("구글 뉴스", GoogleNewsCrawler()),
    ]
    
    results = {}
    
    for name, crawler in crawlers:
        print(f"\n📋 {name} 크롤러 테스트 중...")
        
        try:
            async with crawler:
                articles = await crawler.crawl_company_news(test_company, days_back=1)
                
                results[name] = {
                    "success": True,
                    "articles_count": len(articles),
                    "sample_titles": [article.title for article in articles[:3]]
                }
                
                print(f"✅ {name} 테스트 성공: {len(articles)}개 기사 수집")
                
                # 샘플 기사 제목 출력
                if articles:
                    print("   샘플 기사:")
                    for i, article in enumerate(articles[:3], 1):
                        print(f"   {i}. {article.title[:50]}...")
                
        except Exception as e:
            print(f"❌ {name} 테스트 실패: {e}")
            results[name] = {
                "success": False,
                "error": str(e),
                "articles_count": 0
            }
    
    return results


async def test_crawling_manager():
    """크롤링 매니저 테스트"""
    print("\n🔍 크롤링 매니저 테스트 시작...")
    
    try:
        # 데이터베이스에서 테스트 회사 조회
        db = next(get_db())
        
        try:
            test_company = db.query(Company).filter(
                Company.name == "삼성전자",
                Company.is_active == True
            ).first()
            
            if not test_company:
                print("❌ 테스트 회사 '삼성전자'를 찾을 수 없습니다")
                print("💡 먼저 데이터베이스를 초기화해주세요: python scripts/init_db.py")
                return {"success": False, "error": "테스트 회사 없음"}
            
            print(f"📋 회사 정보: {test_company.name} ({test_company.stock_code})")
            
            # 크롤링 매니저로 테스트
            manager = get_crawling_manager()
            result = await manager.crawl_company_news(test_company, days_back=1, db=db)
            
            if result.get("success"):
                print(f"✅ 크롤링 매니저 테스트 성공")
                print(f"   - 수집된 기사: {result.get('articles_found', 0)}개")
                print(f"   - 중복 제거 후: {result.get('articles_unique', 0)}개")
                print(f"   - 저장된 기사: {result.get('articles_saved', 0)}개")
                
                # 소스별 결과
                source_results = result.get('source_results', {})
                for source, source_result in source_results.items():
                    status = "성공" if source_result.get('success') else "실패"
                    articles = source_result.get('articles', 0)
                    print(f"   - {source}: {status} ({articles}개)")
                
                return result
            else:
                print(f"❌ 크롤링 매니저 테스트 실패: {result.get('error')}")
                return result
                
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 크롤링 매니저 테스트 오류: {e}")
        return {"success": False, "error": str(e)}


async def test_crawling_status():
    """크롤링 상태 조회 테스트"""
    print("\n🔍 크롤링 상태 조회 테스트...")
    
    try:
        manager = get_crawling_manager()
        status = await manager.get_crawling_status()
        
        print("✅ 크롤링 상태 조회 성공")
        print(f"   - 최근 24시간 작업 수: {status.get('summary', {}).get('total_jobs', 0)}개")
        print(f"   - 성공률: {status.get('summary', {}).get('success_rate', 0):.1f}%")
        print(f"   - 총 수집 기사: {status.get('summary', {}).get('total_articles', 0)}개")
        
        return status
        
    except Exception as e:
        print(f"❌ 크롤링 상태 조회 실패: {e}")
        return {"error": str(e)}


def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("🔍 데이터베이스 연결 테스트...")
    
    try:
        db = next(get_db())
        
        try:
            # 회사 수 조회
            company_count = db.query(Company).count()
            active_companies = db.query(Company).filter(Company.is_active == True).count()
            
            print(f"✅ 데이터베이스 연결 성공")
            print(f"   - 전체 회사 수: {company_count}개")
            print(f"   - 활성 회사 수: {active_companies}개")
            
            if active_companies == 0:
                print("⚠️  활성 회사가 없습니다. 데이터베이스를 초기화해주세요.")
                return False
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print("💡 데이터베이스가 실행 중인지 확인하고 초기화해주세요:")
        print("   docker-compose up -d db")
        print("   python scripts/init_db.py")
        return False


async def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("멀티 스테이크홀더 센티멘트 분석 플랫폼 - 크롤링 시스템 테스트")
    print("=" * 60)
    
    # 로깅 설정
    setup_logging()
    
    # 1. 데이터베이스 연결 테스트
    if not test_database_connection():
        print("\n❌ 데이터베이스 연결 실패로 테스트를 중단합니다.")
        return 1
    
    # 2. 개별 크롤러 테스트
    crawler_results = await test_individual_crawlers()
    
    # 3. 크롤링 매니저 테스트
    manager_result = await test_crawling_manager()
    
    # 4. 크롤링 상태 조회 테스트
    status_result = await test_crawling_status()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    # 크롤러별 결과
    print("📊 크롤러별 결과:")
    total_articles = 0
    successful_crawlers = 0
    
    for name, result in crawler_results.items():
        if result["success"]:
            successful_crawlers += 1
            articles = result["articles_count"]
            total_articles += articles
            print(f"   ✅ {name}: {articles}개 기사")
        else:
            print(f"   ❌ {name}: {result['error']}")
    
    print(f"\n📈 전체 통계:")
    print(f"   - 성공한 크롤러: {successful_crawlers}/{len(crawler_results)}개")
    print(f"   - 총 수집 기사: {total_articles}개")
    
    # 매니저 결과
    if manager_result.get("success"):
        print(f"   - 매니저 테스트: ✅ 성공 ({manager_result.get('articles_saved', 0)}개 저장)")
    else:
        print(f"   - 매니저 테스트: ❌ 실패")
    
    # 전체 성공 여부
    all_success = (
        successful_crawlers > 0 and 
        manager_result.get("success", False)
    )
    
    if all_success:
        print("\n🎉 크롤링 시스템 테스트가 성공적으로 완료되었습니다!")
        print("\n💡 다음 단계:")
        print("   1. Celery 워커 시작: celery -A app.tasks.celery_app worker --loglevel=info")
        print("   2. 크롤링 API 테스트: python scripts/test_api.py")
        print("   3. 웹 인터페이스에서 크롤링 시작")
        return 0
    else:
        print("\n⚠️  일부 테스트가 실패했습니다.")
        print("   - 네트워크 연결을 확인해주세요")
        print("   - 뉴스 사이트 접근이 차단되었을 수 있습니다")
        print("   - VPN 사용을 고려해보세요")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)