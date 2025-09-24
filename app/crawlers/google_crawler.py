"""
구글 뉴스 크롤러
"""

import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from urllib.parse import quote, urljoin
import re
from bs4 import BeautifulSoup

from app.crawlers.base import BaseCrawler, NewsArticle
from app.core.logging import logger
from app.core.config import settings
from database.models import NewsSource, Company


class GoogleNewsCrawler(BaseCrawler):
    """구글 뉴스 크롤러"""
    
    def __init__(self):
        super().__init__(NewsSource.GOOGLE)
        self.base_url = "https://news.google.com/search"
        self.rss_url = "https://news.google.com/rss/search"
    
    async def search_articles(self, company: Company, days_back: int = 7) -> List[NewsArticle]:
        """구글 뉴스에서 회사 관련 기사 검색"""
        articles = []
        
        try:
            # 검색 키워드 준비
            search_keywords = [company.name]
            if company.stock_code:
                search_keywords.append(company.stock_code)
            
            for keyword in search_keywords:
                keyword_articles = await self._search_by_keyword(keyword, days_back)
                articles.extend(keyword_articles)
            
            # 중복 제거 (URL 기준)
            seen_urls = set()
            unique_articles = []
            for article in articles:
                if article.url not in seen_urls:
                    seen_urls.add(article.url)
                    unique_articles.append(article)
            
            logger.info(f"구글 뉴스 검색 완료: {len(unique_articles)}개 (중복 제거 후)")
            return unique_articles
            
        except Exception as e:
            logger.error(f"구글 뉴스 검색 오류: {e}")
            return []
    
    async def _search_by_keyword(self, keyword: str, days_back: int) -> List[NewsArticle]:
        """키워드로 뉴스 검색 (RSS 사용)"""
        articles = []
        
        try:
            # RSS 검색 URL 생성
            search_query = f"{keyword} when:{days_back}d"
            rss_url = f"{self.rss_url}?q={quote(search_query)}&hl=ko&gl=KR&ceid=KR:ko"
            
            # RSS 피드 가져오기
            rss_content = await self.fetch_page(rss_url)
            if not rss_content:
                return []
            
            # RSS 파싱
            articles = self._parse_rss_feed(rss_content)
            
            logger.info(f"키워드 '{keyword}' RSS 검색 결과: {len(articles)}개")
            return articles
            
        except Exception as e:
            logger.error(f"키워드 검색 오류 ({keyword}): {e}")
            return []
    
    def _parse_rss_feed(self, rss_content: str) -> List[NewsArticle]:
        """RSS 피드 파싱"""
        articles = []
        
        try:
            soup = BeautifulSoup(rss_content, 'xml')
            
            # RSS 아이템들 찾기
            items = soup.find_all('item')
            
            for item in items:
                try:
                    # 제목 추출
                    title_elem = item.find('title')
                    if not title_elem:
                        continue
                    
                    title = self.clean_text(title_elem.get_text())
                    
                    # 링크 추출
                    link_elem = item.find('link')
                    if not link_elem:
                        continue
                    
                    url = link_elem.get_text().strip()
                    
                    # 구글 뉴스 리다이렉트 URL 처리
                    if 'news.google.com' in url:
                        # 실제 뉴스 URL 추출 시도
                        url = self._extract_real_url(url)
                    
                    # 설명 (요약) 추출
                    description_elem = item.find('description')
                    summary = self.clean_text(description_elem.get_text()) if description_elem else ""
                    
                    # 발행 시간 추출
                    pub_date_elem = item.find('pubDate')
                    published_date = None
                    if pub_date_elem:
                        date_text = pub_date_elem.get_text()
                        published_date = self._parse_rss_date(date_text)
                    
                    # 언론사 정보 (RSS에서는 제한적)
                    source_elem = item.find('source')
                    author = self.clean_text(source_elem.get_text()) if source_elem else None
                    
                    article = NewsArticle(
                        title=title,
                        content=summary,  # RSS에서는 요약만 제공
                        url=url,
                        author=author,
                        published_date=published_date,
                        source=self.source,
                        summary=summary
                    )
                    
                    if self.validate_article_basic(article):
                        articles.append(article)
                
                except Exception as e:
                    logger.warning(f"RSS 아이템 파싱 오류: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"RSS 피드 파싱 오류: {e}")
            return []
    
    def _extract_real_url(self, google_url: str) -> str:
        """구글 뉴스 리다이렉트 URL에서 실제 URL 추출"""
        try:
            # URL 파라미터에서 실제 URL 찾기
            import urllib.parse as urlparse
            
            parsed = urlparse.urlparse(google_url)
            query_params = urlparse.parse_qs(parsed.query)
            
            # 'url' 파라미터에서 실제 URL 추출
            if 'url' in query_params:
                return query_params['url'][0]
            
            # 다른 방법으로 URL 추출 시도
            if 'articles/' in google_url:
                # 구글 뉴스 기사 ID에서 원본 URL 추출은 복잡하므로
                # 일단 구글 URL 그대로 반환
                return google_url
            
            return google_url
            
        except Exception as e:
            logger.warning(f"실제 URL 추출 실패: {google_url} - {e}")
            return google_url
    
    def validate_article_basic(self, article: NewsArticle) -> bool:
        """기본 기사 유효성 검증 (RSS용)"""
        if not article.title or len(article.title.strip()) < 5:
            return False
        
        if not article.url or not self.is_valid_url(article.url):
            return False
        
        return True
    
    async def parse_article_detail(self, url: str) -> Optional[NewsArticle]:
        """기사 상세 내용 파싱"""
        try:
            # 구글 뉴스 URL인 경우 실제 뉴스 사이트로 리다이렉트
            if 'news.google.com' in url:
                # 구글 뉴스에서는 직접 본문을 가져올 수 없으므로
                # RSS에서 제공된 정보만 사용
                return None
            
            html = await self.fetch_page(url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 일반적인 뉴스 사이트 구조로 파싱 시도
            article = self._parse_generic_news_site(soup, url)
            
            if article and self.validate_article(article):
                return article
            else:
                logger.warning(f"기사 파싱 실패 또는 유효성 검증 실패: {url}")
                return None
                
        except Exception as e:
            logger.error(f"기사 상세 파싱 오류 ({url}): {e}")
            return None
    
    def _parse_generic_news_site(self, soup: BeautifulSoup, url: str) -> Optional[NewsArticle]:
        """일반적인 뉴스 사이트 구조 파싱"""
        try:
            # 제목 추출 (다양한 패턴 시도)
            title_selectors = [
                'h1',
                'h2',
                '.title',
                '.headline',
                '[class*="title"]',
                '[class*="headline"]'
            ]
            
            title = None
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = self.clean_text(title_elem.get_text())
                    if title and len(title) > 5:
                        break
            
            if not title:
                return None
            
            # 본문 추출 (다양한 패턴 시도)
            content_selectors = [
                'article',
                '.article-content',
                '.content',
                '.article-body',
                '[class*="content"]',
                '[class*="article"]',
                'main'
            ]
            
            content = None
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # 불필요한 요소 제거
                    for elem in content_elem.find_all(['script', 'style', 'nav', 'aside']):
                        elem.decompose()
                    
                    content = self.clean_text(content_elem.get_text())
                    if content and len(content) > 100:
                        break
            
            if not content:
                return None
            
            # 기자 정보 추출
            author_selectors = [
                '.author',
                '.byline',
                '.reporter',
                '[class*="author"]',
                '[class*="byline"]'
            ]
            
            author = None
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = self.clean_text(author_elem.get_text())
                    if author:
                        break
            
            # 발행 시간 추출
            date_selectors = [
                'time',
                '.date',
                '.published',
                '[datetime]',
                '[class*="date"]',
                '[class*="time"]'
            ]
            
            published_date = None
            for selector in date_selectors:
                date_elem = soup.select_one(selector)
                if date_elem:
                    date_text = date_elem.get('datetime') or date_elem.get_text()
                    published_date = self.normalize_date(date_text)
                    if published_date:
                        break
            
            # 키워드 추출
            keywords = self.extract_keywords(title, content)
            
            # 요약 생성
            summary = self.generate_summary(content)
            
            return NewsArticle(
                title=title,
                content=content,
                url=url,
                author=author,
                published_date=published_date,
                source=self.source,
                keywords=keywords,
                summary=summary
            )
            
        except Exception as e:
            logger.error(f"일반 뉴스 사이트 파싱 오류: {e}")
            return None
    
    def _parse_rss_date(self, date_text: str) -> Optional[datetime]:
        """RSS 날짜 형식 파싱"""
        if not date_text:
            return None
        
        try:
            # RSS 표준 날짜 형식들
            rss_formats = [
                '%a, %d %b %Y %H:%M:%S %Z',
                '%a, %d %b %Y %H:%M:%S %z',
                '%Y-%m-%dT%H:%M:%S%z',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%d %H:%M:%S',
            ]
            
            for fmt in rss_formats:
                try:
                    return datetime.strptime(date_text.strip(), fmt)
                except ValueError:
                    continue
            
            # 기본 날짜 파싱 시도
            return self.normalize_date(date_text)
            
        except Exception as e:
            logger.warning(f"RSS 날짜 파싱 실패: {date_text} - {e}")
            return None