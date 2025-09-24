#!/usr/bin/env python3
"""
센티멘트 분석 시스템 테스트 스크립트
"""

import sys
import os
import asyncio
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.ml.korean_analyzer import KoreanSentimentAnalyzer
from app.ml.analysis_manager import get_analysis_manager
from app.ml.base_analyzer import AnalysisInput
from app.core.database import get_db
from app.core.logging import setup_logging, logger
from database.models import NewsArticle, Company


async def test_korean_analyzer():
    """한국어 센티멘트 분석기 테스트"""
    print("🔍 한국어 센티멘트 분석기 테스트 시작...")
    
    analyzer = KoreanSentimentAnalyzer()
    
    try:
        # 모델 로드 테스트
        print("📋 모델 로드 테스트 중...")
        load_success = await analyzer.load_model()
        
        if not load_success:
            print("❌ 모델 로드 실패")
            return False
        
        print("✅ 모델 로드 성공")
        
        # 테스트 케이스들
        test_cases = [
            {
                "title": "삼성전자 실적 호조",
                "content": "삼성전자가 3분기 실적에서 예상을 뛰어넘는 성과를 거두었습니다. 매출과 영업이익 모두 전년 동기 대비 크게 증가했습니다.",
                "company": "삼성전자",
                "expected_sentiment": "positive"
            },
            {
                "title": "제품 리콜 발표",
                "content": "안전상의 문제로 인해 제품 리콜이 발표되었습니다. 고객들의 불만이 커지고 있으며 회사 이미지에 타격이 예상됩니다.",
                "company": "테스트회사",
                "expected_sentiment": "negative"
            },
            {
                "title": "정기 주주총회 개최",
                "content": "오늘 정기 주주총회가 개최되었습니다. 작년 사업 실적과 올해 계획에 대해 논의했습니다.",
                "company": "테스트회사",
                "expected_sentiment": "neutral"
            },
            {
                "title": "신제품 출시 성공",
                "content": "새로 출시된 제품이 고객들로부터 뜨거운 반응을 얻고 있습니다. 혁신적인 기능과 뛰어난 품질로 시장에서 큰 호응을 받고 있습니다.",
                "company": "테스트회사",
                "expected_sentiment": "very_positive"
            }
        ]
        
        print(f"\n📋 {len(test_cases)}개 테스트 케이스 분석 중...")
        
        results = []
        for i, case in enumerate(test_cases, 1):
            print(f"\n{i}. 테스트 케이스: {case['title']}")
            
            # 분석 입력 생성
            analysis_input = AnalysisInput(
                title=case["title"],
                content=case["content"],
                company_name=case["company"]
            )
            
            # 센티멘트 분석
            sentiment_result = await analyzer.analyze_sentiment(analysis_input)
            
            # 스테이크홀더 분류
            stakeholder_result = await analyzer.classify_stakeholder(analysis_input)
            
            print(f"   센티멘트: {sentiment_result.sentiment_score.value} (신뢰도: {sentiment_result.confidence:.3f})")
            print(f"   스테이크홀더: {stakeholder_result.stakeholder_type.value} (신뢰도: {stakeholder_result.confidence:.3f})")
            print(f"   키워드: {', '.join(sentiment_result.keywords[:5])}")
            
            results.append({
                "case": case,
                "sentiment_result": sentiment_result,
                "stakeholder_result": stakeholder_result
            })
        
        print(f"\n✅ 센티멘트 분석기 테스트 완료: {len(results)}개 케이스 처리")
        return results
        
    except Exception as e:
        print(f"❌ 센티멘트 분석기 테스트 실패: {e}")
        return False


async def test_analysis_manager():
    """분석 매니저 테스트"""
    print("\n🔍 분석 매니저 테스트 시작...")
    
    try:
        manager = get_analysis_manager()
        
        # 초기화 테스트
        print("📋 분석 매니저 초기화 중...")
        init_success = await manager.initialize()
        
        if not init_success:
            print("❌ 분석 매니저 초기화 실패")
            return False
        
        print("✅ 분석 매니저 초기화 성공")
        
        # 통계 조회 테스트
        print("📋 분석 통계 조회 테스트 중...")
        statistics = await manager.get_analysis_statistics(days=30)
        
        if "error" in statistics:
            print(f"⚠️  통계 조회 오류: {statistics['error']}")
        else:
            print("✅ 분석 통계 조회 성공")
            print(f"   - 전체 기사: {statistics.get('total_articles', 0)}개")
            print(f"   - 분석된 기사: {statistics.get('analyzed_articles', 0)}개")
            print(f"   - 완료율: {statistics.get('completion_rate', 0)}%")
        
        return True
        
    except Exception as e:
        print(f"❌ 분석 매니저 테스트 실패: {e}")
        return False


async def test_database_analysis():
    """데이터베이스 기사 분석 테스트"""
    print("\n🔍 데이터베이스 기사 분석 테스트 시작...")
    
    try:
        db = next(get_db())
        
        try:
            # 분석되지 않은 기사 조회
            pending_articles = db.query(NewsArticle).filter(
                NewsArticle.sentiment_score.is_(None)
            ).limit(5).all()
            
            if not pending_articles:
                print("ℹ️  분석할 기사가 없습니다")
                return True
            
            print(f"📋 {len(pending_articles)}개 기사 분석 테스트 중...")
            
            manager = get_analysis_manager()
            
            # 분석기 초기화
            if not manager.analyzer.is_loaded:
                await manager.initialize()
            
            # 각 기사 분석
            for i, article in enumerate(pending_articles, 1):
                print(f"\n{i}. 기사 분석: {article.title[:50]}...")
                
                result = await manager.analyze_single_article(article.id, db)
                
                if result.get("success"):
                    sentiment = result["sentiment_result"]["sentiment_score"]
                    stakeholder = result["stakeholder_result"]["stakeholder_type"]
                    print(f"   ✅ 분석 완료 - 센티멘트: {sentiment}, 스테이크홀더: {stakeholder}")
                else:
                    print(f"   ❌ 분석 실패: {result.get('error')}")
            
            print(f"\n✅ 데이터베이스 기사 분석 테스트 완료")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 데이터베이스 기사 분석 테스트 실패: {e}")
        return False


def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("🔍 데이터베이스 연결 테스트...")
    
    try:
        db = next(get_db())
        
        try:
            # 기사 수 조회
            total_articles = db.query(NewsArticle).count()
            analyzed_articles = db.query(NewsArticle).filter(
                NewsArticle.sentiment_score.isnot(None)
            ).count()
            
            print(f"✅ 데이터베이스 연결 성공")
            print(f"   - 전체 기사 수: {total_articles}개")
            print(f"   - 분석된 기사 수: {analyzed_articles}개")
            
            if total_articles == 0:
                print("⚠️  기사가 없습니다. 먼저 크롤링을 실행해주세요.")
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
    print("멀티 스테이크홀더 센티멘트 분석 플랫폼 - 센티멘트 분석 시스템 테스트")
    print("=" * 60)
    
    # 로깅 설정
    setup_logging()
    
    # 1. 데이터베이스 연결 테스트
    if not test_database_connection():
        print("\n❌ 데이터베이스 연결 실패로 일부 테스트를 건너뜁니다.")
        db_available = False
    else:
        db_available = True
    
    # 2. 한국어 분석기 테스트
    analyzer_results = await test_korean_analyzer()
    
    # 3. 분석 매니저 테스트
    manager_success = await test_analysis_manager()
    
    # 4. 데이터베이스 기사 분석 테스트 (DB 사용 가능한 경우)
    db_analysis_success = True
    if db_available:
        db_analysis_success = await test_database_analysis()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    # 분석기 결과
    if analyzer_results:
        print("📊 센티멘트 분석기 결과:")
        print(f"   ✅ 모델 로드: 성공")
        print(f"   ✅ 테스트 케이스: {len(analyzer_results)}개 처리")
        
        # 샘플 결과 출력
        if analyzer_results:
            sample = analyzer_results[0]
            print(f"   📝 샘플 결과:")
            print(f"      제목: {sample['case']['title']}")
            print(f"      센티멘트: {sample['sentiment_result'].sentiment_score.value}")
            print(f"      신뢰도: {sample['sentiment_result'].confidence:.3f}")
    else:
        print("❌ 센티멘트 분석기: 실패")
    
    # 매니저 결과
    if manager_success:
        print("   ✅ 분석 매니저: 성공")
    else:
        print("   ❌ 분석 매니저: 실패")
    
    # DB 분석 결과
    if db_available:
        if db_analysis_success:
            print("   ✅ 데이터베이스 분석: 성공")
        else:
            print("   ❌ 데이터베이스 분석: 실패")
    else:
        print("   ⚠️  데이터베이스 분석: 건너뜀")
    
    # 전체 성공 여부
    all_success = (
        analyzer_results and 
        manager_success and 
        (db_analysis_success or not db_available)
    )
    
    if all_success:
        print("\n🎉 센티멘트 분석 시스템 테스트가 성공적으로 완료되었습니다!")
        print("\n💡 다음 단계:")
        print("   1. Celery 워커 시작: celery -A app.tasks.celery_app worker --loglevel=info")
        print("   2. 센티멘트 분석 API 테스트")
        print("   3. 웹 인터페이스에서 분석 시작")
        return 0
    else:
        print("\n⚠️  일부 테스트가 실패했습니다.")
        print("   - 모델 다운로드에 시간이 걸릴 수 있습니다")
        print("   - 인터넷 연결을 확인해주세요")
        print("   - GPU 사용 시 CUDA 설정을 확인해주세요")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)