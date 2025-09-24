#!/usr/bin/env python3
"""
스테이크홀더 분석 시스템 테스트 스크립트
"""

import sys
import os
import asyncio
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.stakeholders.customer_analyzer import CustomerAnalyzer
from app.stakeholders.investor_analyzer import InvestorAnalyzer
from app.stakeholders.employee_analyzer import EmployeeAnalyzer
from app.stakeholders.stakeholder_manager import get_stakeholder_manager
from app.core.database import get_db
from app.core.logging import setup_logging, logger
from database.models import Company, NewsArticle, StakeholderType


async def test_individual_analyzers():
    """개별 스테이크홀더 분석기 테스트"""
    print("🔍 개별 스테이크홀더 분석기 테스트 시작...")
    
    # 테스트 데이터 생성
    test_articles = [
        {
            "title": "고객 만족도 조사 결과 발표",
            "content": "고객들이 제품 품질과 서비스에 대해 높은 만족도를 보였습니다. 특히 배송 서비스와 고객 지원이 우수하다는 평가를 받았습니다.",
            "sentiment_score": "positive",
            "sentiment_confidence": 0.85,
            "keywords": ["고객", "만족도", "품질", "서비스", "배송"]
        },
        {
            "title": "3분기 실적 발표",
            "content": "3분기 매출이 전년 동기 대비 15% 증가했으며, 영업이익도 크게 개선되었습니다. 투자자들의 긍정적인 반응이 이어지고 있습니다.",
            "sentiment_score": "very_positive",
            "sentiment_confidence": 0.92,
            "keywords": ["실적", "매출", "영업이익", "투자자", "증가"]
        },
        {
            "title": "직원 복지 제도 개선",
            "content": "회사가 직원들의 워라밸 개선을 위해 유연근무제를 도입하고 복리후생을 확대한다고 발표했습니다. 직원들의 만족도가 높아질 것으로 예상됩니다.",
            "sentiment_score": "positive",
            "sentiment_confidence": 0.78,
            "keywords": ["직원", "복지", "워라밸", "유연근무", "복리후생"]
        }
    ]
    
    analyzers = [
        ("고객 분석기", CustomerAnalyzer(), test_articles[:1]),
        ("투자자 분석기", InvestorAnalyzer(), test_articles[1:2]),
        ("직원 분석기", EmployeeAnalyzer(), test_articles[2:3])
    ]
    
    results = {}
    
    for name, analyzer, articles in analyzers:
        print(f"\n📋 {name} 테스트 중...")
        
        try:
            # 인사이트 분석
            insight = analyzer.analyze_stakeholder_insight(articles)
            
            results[name] = {
                "success": True,
                "insight": insight
            }
            
            print(f"✅ {name} 테스트 성공")
            print(f"   - 센티멘트: {insight.sentiment_score.value}")
            print(f"   - 신뢰도: {insight.confidence:.3f}")
            print(f"   - 영향도: {insight.impact_level.value}")
            print(f"   - 긴급도: {insight.urgency_level.value}")
            print(f"   - 주요 관심사: {', '.join(insight.key_concerns[:3])}")
            print(f"   - 액션 아이템: {len(insight.action_items)}개")
            
        except Exception as e:
            print(f"❌ {name} 테스트 실패: {e}")
            results[name] = {
                "success": False,
                "error": str(e)
            }
    
    return results


async def test_stakeholder_manager():
    """스테이크홀더 매니저 테스트"""
    print("\n🔍 스테이크홀더 매니저 테스트 시작...")
    
    try:
        manager = get_stakeholder_manager()
        
        # 사용 가능한 스테이크홀더 조회
        print("📋 사용 가능한 스테이크홀더 조회 중...")
        stakeholders = manager.get_available_stakeholders()
        
        print(f"✅ 스테이크홀더 조회 성공: {len(stakeholders)}개")
        for stakeholder in stakeholders:
            status = "✅" if stakeholder["analyzer_available"] else "⚠️"
            print(f"   {status} {stakeholder['name']}: {stakeholder['description'][:50]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 스테이크홀더 매니저 테스트 실패: {e}")
        return False


async def test_database_analysis():
    """데이터베이스 기반 스테이크홀더 분석 테스트"""
    print("\n🔍 데이터베이스 기반 분석 테스트 시작...")
    
    try:
        db = next(get_db())
        
        try:
            # 테스트용 회사 조회
            test_company = db.query(Company).filter(
                Company.name == "삼성전자",
                Company.is_active == True
            ).first()
            
            if not test_company:
                print("⚠️  테스트 회사 '삼성전자'를 찾을 수 없습니다")
                return False
            
            # 스테이크홀더별 기사 수 확인
            stakeholder_counts = {}
            for stakeholder_type in StakeholderType:
                count = db.query(NewsArticle).filter(
                    NewsArticle.company_id == test_company.id,
                    NewsArticle.stakeholder_type == stakeholder_type,
                    NewsArticle.sentiment_score.isnot(None)
                ).count()
                stakeholder_counts[stakeholder_type.value] = count
            
            print(f"📋 회사: {test_company.name}")
            print("   스테이크홀더별 기사 수:")
            for stakeholder, count in stakeholder_counts.items():
                print(f"     - {stakeholder}: {count}개")
            
            total_articles = sum(stakeholder_counts.values())
            if total_articles == 0:
                print("⚠️  분석할 기사가 없습니다. 먼저 크롤링과 센티멘트 분석을 실행해주세요.")
                return False
            
            # 스테이크홀더 인사이트 분석 테스트
            print("\n📋 스테이크홀더 인사이트 분석 테스트 중...")
            manager = get_stakeholder_manager()
            
            # 고객 분석 (데이터가 있는 경우)
            if stakeholder_counts.get("customer", 0) > 0:
                result = await manager.analyze_stakeholder_insights(
                    test_company.id, StakeholderType.CUSTOMER, 30, db
                )
                
                if result.get("success"):
                    customer_insight = result["insights"]["customer"]
                    print(f"   ✅ 고객 분석 성공")
                    print(f"      - 센티멘트: {customer_insight['sentiment_score']}")
                    print(f"      - 영향도: {customer_insight['impact_level']}")
                    print(f"      - 액션 아이템: {len(customer_insight['action_items'])}개")
                else:
                    print(f"   ❌ 고객 분석 실패: {result.get('error')}")
            
            print("✅ 데이터베이스 기반 분석 테스트 완료")
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 데이터베이스 기반 분석 테스트 실패: {e}")
        return False


def test_database_connection():
    """데이터베이스 연결 테스트"""
    print("🔍 데이터베이스 연결 테스트...")
    
    try:
        db = next(get_db())
        
        try:
            # 회사 수 조회
            company_count = db.query(Company).count()
            
            # 스테이크홀더별 기사 수 조회
            stakeholder_articles = {}
            for stakeholder_type in StakeholderType:
                count = db.query(NewsArticle).filter(
                    NewsArticle.stakeholder_type == stakeholder_type,
                    NewsArticle.sentiment_score.isnot(None)
                ).count()
                stakeholder_articles[stakeholder_type.value] = count
            
            total_analyzed = sum(stakeholder_articles.values())
            
            print(f"✅ 데이터베이스 연결 성공")
            print(f"   - 등록된 회사 수: {company_count}개")
            print(f"   - 분석된 기사 수: {total_analyzed}개")
            
            if total_analyzed == 0:
                print("⚠️  분석된 기사가 없습니다.")
                print("💡 다음 순서로 데이터를 준비해주세요:")
                print("   1. python scripts/init_db.py")
                print("   2. python scripts/test_crawling.py")
                print("   3. python scripts/test_sentiment.py")
                return False
            
            return True
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False


async def main():
    """메인 테스트 함수"""
    print("=" * 60)
    print("멀티 스테이크홀더 센티멘트 분석 플랫폼 - 스테이크홀더 분석 시스템 테스트")
    print("=" * 60)
    
    # 로깅 설정
    setup_logging()
    
    # 1. 데이터베이스 연결 테스트
    db_available = test_database_connection()
    
    # 2. 개별 분석기 테스트
    analyzer_results = await test_individual_analyzers()
    
    # 3. 스테이크홀더 매니저 테스트
    manager_success = await test_stakeholder_manager()
    
    # 4. 데이터베이스 기반 분석 테스트 (DB 사용 가능한 경우)
    db_analysis_success = True
    if db_available:
        db_analysis_success = await test_database_analysis()
    
    # 결과 요약
    print("\n" + "=" * 60)
    print("테스트 결과 요약")
    print("=" * 60)
    
    # 분석기 결과
    print("📊 스테이크홀더 분석기 결과:")
    successful_analyzers = 0
    for name, result in analyzer_results.items():
        if result["success"]:
            successful_analyzers += 1
            insight = result["insight"]
            print(f"   ✅ {name}: {insight.sentiment_score.value} (신뢰도: {insight.confidence:.3f})")
        else:
            print(f"   ❌ {name}: {result['error']}")
    
    print(f"\n📈 전체 통계:")
    print(f"   - 성공한 분석기: {successful_analyzers}/{len(analyzer_results)}개")
    
    # 매니저 결과
    if manager_success:
        print("   ✅ 스테이크홀더 매니저: 성공")
    else:
        print("   ❌ 스테이크홀더 매니저: 실패")
    
    # DB 분석 결과
    if db_available:
        if db_analysis_success:
            print("   ✅ 데이터베이스 분석: 성공")
        else:
            print("   ❌ 데이터베이스 분석: 실패")
    else:
        print("   ⚠️  데이터베이스 분석: 건너뜀 (데이터 부족)")
    
    # 전체 성공 여부
    all_success = (
        successful_analyzers > 0 and 
        manager_success and 
        (db_analysis_success or not db_available)
    )
    
    if all_success:
        print("\n🎉 스테이크홀더 분석 시스템 테스트가 성공적으로 완료되었습니다!")
        print("\n💡 다음 단계:")
        print("   1. 스테이크홀더 분석 API 테스트")
        print("   2. 웹 인터페이스에서 인사이트 확인")
        print("   3. 액션 아이템 기반 대응 방안 수립")
        
        print("\n🔧 사용 가능한 API:")
        print("   GET  /api/v1/stakeholders/types")
        print("   GET  /api/v1/stakeholders/insights/{company_id}")
        print("   GET  /api/v1/stakeholders/comparison/{company_id}")
        print("   GET  /api/v1/stakeholders/action-items/{company_id}")
        
        return 0
    else:
        print("\n⚠️  일부 테스트가 실패했습니다.")
        print("   - 데이터가 충분한지 확인해주세요")
        print("   - 크롤링과 센티멘트 분석이 완료되었는지 확인해주세요")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)