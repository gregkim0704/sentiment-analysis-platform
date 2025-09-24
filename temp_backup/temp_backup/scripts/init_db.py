#!/usr/bin/env python3
"""
데이터베이스 초기화 스크립트
"""

import sys
import os
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from database.database import init_database, check_database_health
from database.models import Base

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('logs/init_db.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """메인 함수"""
    try:
        logger.info("=" * 60)
        logger.info("멀티 스테이크홀더 센티멘트 분석 플랫폼 DB 초기화 시작")
        logger.info("=" * 60)
        
        # 로그 디렉토리 생성
        os.makedirs('logs', exist_ok=True)
        
        # 데이터베이스 초기화
        logger.info("데이터베이스 초기화 중...")
        init_database()
        
        # 데이터베이스 상태 확인
        logger.info("데이터베이스 상태 확인 중...")
        health_status = check_database_health()
        
        if health_status["status"] == "healthy":
            logger.info("✅ 데이터베이스 초기화 성공!")
            logger.info(f"   - 테이블 수: {health_status['table_count']}")
            logger.info(f"   - 활성 연결: {health_status['active_connections']}")
            logger.info(f"   - 데이터베이스: {health_status['database_url']}")
        else:
            logger.error("❌ 데이터베이스 상태 확인 실패")
            logger.error(f"   - 오류: {health_status.get('error', 'Unknown error')}")
            return 1
        
        logger.info("=" * 60)
        logger.info("초기화 완료! 다음 단계:")
        logger.info("1. 관리자 계정으로 로그인: admin@sentiment-analysis.com / admin123")
        logger.info("2. 회사 정보 확인 및 추가")
        logger.info("3. 뉴스 크롤링 시작")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)