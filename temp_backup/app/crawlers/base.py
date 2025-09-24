"""
크롤러 기본 클래스
"""

import asyncio
import aiohttp
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import time
import random

from app.core.logging import logger
from app.core.config import settings
from database.models import NewsSource, Company


@dataclass
class NewsArticle:
    """뉴스 기사 데이터 클래스"""
    title: str
    content: str
    url: str
    author: Optional[str] = None
    published_date: Optional[datetime] = None
    source: Optional[NewsSource] = None
    company_name: Optional[str] = None
    keywords: Optional[List[str]] = None
    summary: Optional[str] = None


class BaseCrawler(ABC):
    """크롤러 기본 클래스"""
    
    def __init__(self, source: NewsSource):
        self.source = source
        self.session: Optional[aiohttp.ClientSession] = None
        self.delay = settings.CRAWLING_DELAY_SECONDS
        self.timeout = settings.CRAWLING_TIMEOUT_SECONDS
        self.max_articles = settings.MAX_ARTICLES_PER_CRAWLING
        self.user_agent = settings.USER_AGENT
        
        # 요청 헤더 설정
        self.headers = {
            'User-Agent': self.user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
    
    async def __aenter__(self):
        """비동기 컨텍스트 매니저 진입"""
        connector = aiohttp.TCPConnector(
            limit=10,  # 최대 연결 수
            limit_per_host=5,  # 호스트당 최대 연결 수
            ttl_dns_cache=300,  # DNS 캐시 TTL
            use_dns_cache=True,
        )
        
        timeout = aiohttp.ClientTimeout(total=self.timeout)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """비동기 컨텍스트 매니저 종료"""
        if self.session:
            await self.session.close()
    
    async def fetch_page(self, url: str, **kwargs) -> Optional[str]:
        """웹 페이지 가져오기"""
        try:
            # 요청 간 지연
            await asyncio.sleep(self.delay + random.uniform(0, 1))
            
            async with self.session.get(url, **kwargs) as response:
                if response.status == 200:
                    content = await response.text()
                    logger.debug(f"페이지 가져오기 성공: {url}")
                    return content
                else:
                    logger.warning(f"페이지 가져오기 실패: {url} (상태코드: {response.status})")
                    return None
                    
        except asyncio.TimeoutError:
            logger.error(f"페이지 가져오기 타임아웃: {url}")
            return None
        except Exception as e:
            logger.error(f"페이지 가져오기 오류: {url} - {e}")
            return None
    
    def clean_text(self, text: str) -> str:
        """텍스트 정제"""
        if not text:
            return ""
        
        # HTML 태그 제거
        import re
        text = re.sub(r'<[^>]+>', '', text)
        
        # 특수 문자 정제
        text = re.sub(r'&nbsp;|&amp;|&lt;|&gt;|&quot;|&#\d+;', ' ', text)
        
        # 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def extract_keywords(self, title: str, content: str) -> List[str]:
        """키워드 추출 (기본 구현)"""
        # 간단한 키워드 추출 (향후 NLP 모델로 개선)
        import re
        
        text = f"{title} {content}".lower()
        
        # 한글, 영문 단어 추출
        words = re.findall(r'[가-힣]{2,}|[a-zA-Z]{3,}', text)
        
        # 빈도 계산
        from collections import Counter
        word_counts = Counter(words)
        
        # 상위 10개 키워드 반환
        keywords = [word for word, count in word_counts.most_common(10)]
        
        return keywords
    
    def generate_summary(self, content: str, max_length: int = 200) -> str:
        """요약 생성 (기본 구현)"""
        if not content:
            return ""
        
        # 문장 단위로 분할
        sentences = content.split('.')
        
        # 첫 번째 문장들을 조합하여 요약 생성
        summary = ""
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(summary + sentence) < max_length:
                summary += sentence + ". "
            else:
                break
        
        return summary.strip()
    
    def is_relevant_article(self, article: NewsArticle, company: Company) -> bool:
        """기사가 회사와 관련있는지 확인"""
        company_keywords = [
            company.name,
            company.stock_code,
        ]
        
        # 회사 이름의 변형도 확인
        if company.name:
            # 기본 이름
            company_keywords.append(company.name)
            # 공백 제거
            company_keywords.append(company.name.replace(' ', ''))
            # 영문명이 있다면 추가 (향후 확장)
        
        text = f"{article.title} {article.content}".lower()
        
        for keyword in company_keywords:
            if keyword and keyword.lower() in text:
                return True
        
        return False
    
    @abstractmethod
    async def search_articles(self, company: Company, days_back: int = 7) -> List[NewsArticle]:
        """회사 관련 기사 검색 (추상 메서드)"""
        pass
    
    @abstractmethod
    async def parse_article_detail(self, url: str) -> Optional[NewsArticle]:
        """기사 상세 내용 파싱 (추상 메서드)"""
        pass
    
    async def crawl_company_news(self, company: Company, days_back: int = 7) -> List[NewsArticle]:
        """회사 뉴스 크롤링"""
        logger.info(f"{self.source.value} 크롤링 시작: {company.name}")
        
        try:
            # 기사 목록 검색
            articles = await self.search_articles(company, days_back)
            
            if not articles:
                logger.info(f"검색된 기사가 없습니다: {company.name}")
                return []
            
            logger.info(f"검색된 기사 수: {len(articles)}개")
            
            # 기사 상세 내용 가져오기 (병렬 처리)
            detailed_articles = []
            semaphore = asyncio.Semaphore(5)  # 동시 요청 수 제한
            
            async def fetch_detail(article):
                async with semaphore:
                    detailed = await self.parse_article_detail(article.url)
                    if detailed and self.is_relevant_article(detailed, company):
                        detailed.company_name = company.name
                        detailed.source = self.source
                        return detailed
                    return None
            
            # 병렬로 상세 내용 가져오기
            tasks = [fetch_detail(article) for article in articles[:self.max_articles]]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 성공한 결과만 수집
            for result in results:
                if isinstance(result, NewsArticle):
                    detailed_articles.append(result)
                elif isinstance(result, Exception):
                    logger.error(f"기사 상세 가져오기 오류: {result}")
            
            logger.info(f"상세 내용 수집 완료: {len(detailed_articles)}개")
            return detailed_articles
            
        except Exception as e:
            logger.error(f"크롤링 오류 ({company.name}): {e}")
            return []
    
    def validate_article(self, article: NewsArticle) -> bool:
        """기사 데이터 유효성 검증"""
        if not article.title or len(article.title.strip()) < 5:
            return False
        
        if not article.content or len(article.content.strip()) < 50:
            return False
        
        if not article.url or not self.is_valid_url(article.url):
            return False
        
        return True
    
    def is_valid_url(self, url: str) -> bool:
        """URL 유효성 검증"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def normalize_date(self, date_str: str) -> Optional[datetime]:
        """날짜 문자열을 datetime 객체로 변환"""
        if not date_str:
            return None
        
        # 다양한 날짜 형식 처리
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%Y.%m.%d %H:%M:%S',
            '%Y.%m.%d %H:%M',
            '%Y.%m.%d',
            '%m/%d/%Y %H:%M:%S',
            '%m/%d/%Y %H:%M',
            '%m/%d/%Y',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        logger.warning(f"날짜 파싱 실패: {date_str}")
        return None