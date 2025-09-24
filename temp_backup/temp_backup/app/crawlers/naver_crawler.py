"""
네이버 뉴스 크롤러
"""

import asyncio
from typing import List, Optional
from datetime import datetime, timedelta
from urllib.parse import quote, urljoin
import re
from bs4 import BeautifulSoup

from app.crawlers.base import BaseCrawler, NewsArticle
from app.core.logging import logger
from database.models import NewsSource, Company


class NaverNewsCrawler(BaseCrawler):
    """네이버 뉴스 크롤러"""
    
    def __init__(self):
        super().__init__(NewsSource.NAVER)
        self.base_url = "https://search.naver.com/search.naver"
        self.news_base_url = "https://news.naver.com"
    
    async def search_articles(self, company: Company, days_back: int = 7) -> List[NewsArticle]:
        """네이버 뉴스에서 회사 관련 기사 검색"""
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
            
            logger.info(f"네이버 뉴스 검색 완료: {len(unique_articles)}개 (중복 제거 후)")
            return unique_articles
            
        except Exception as e:
            logger.error(f"네이버 뉴스 검색 오류: {e}")
            return []
    
    async def _search_by_keyword(self, keyword: str, days_back: int) -> List[NewsArticle]:
        """키워드로 뉴스 검색"""
        articles = []
        
        try:
            # 검색 파라미터 설정
            params = {
                'where': 'news',
                'query': keyword,
                'sm': 'tab_opt',
                'sort': '1',  # 최신순
                'photo': '0',
                'field': '0',
                'pd': '3',  # 기간 설정
                'ds': (datetime.now() - timedelta(days=days_back)).strftime('%Y.%m.%d'),
                'de': datetime.now().strftime('%Y.%m.%d'),
                'start': '1'
            }
            
            # 여러 페이지 검색 (최대 5페이지)
            for page in range(1, 6):
                params['start'] = (page - 1) * 10 + 1
                
                # 검색 URL 생성
                search_url = f"{self.base_url}?" + "&".join([f"{k}={quote(str(v))}" for k, v in params.items()])
                
                # 검색 결과 페이지 가져오기
                html = await self.fetch_page(search_url)
                if not html:
                    break
                
                # 검색 결과 파싱
                page_articles = self._parse_search_results(html)
                if not page_articles:
                    break
                
                articles.extend(page_articles)
                
                # 요청 간 지연
                await asyncio.sleep(1)
            
            logger.info(f"키워드 '{keyword}' 검색 결과: {len(articles)}개")
            return articles
            
        except Exception as e:
            logger.error(f"키워드 검색 오류 ({keyword}): {e}")
            return []
    
    def _parse_search_results(self, html: str) -> List[NewsArticle]:
        """검색 결과 HTML 파싱"""
        articles = []
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 뉴스 기사 목록 찾기
            news_items = soup.find_all('div', class_='info_group')
            
            for item in news_items:
                try:
                    # 제목과 링크 추출
                    title_elem = item.find('a', class_='news_tit')
                    if not title_elem:
                        continue
                    
                    title = self.clean_text(title_elem.get_text())
                    url = title_elem.get('href')
                    
                    if not title or not url:
                        continue
                    
                    # 언론사 정보
                    press_elem = item.find('a', class_='info press')
                    author = self.clean_text(press_elem.get_text()) if press_elem else None
                    
                    # 발행 시간
                    date_elem = item.find('span', class_='info')
                    published_date = None
                    if date_elem:
                        date_text = self.clean_text(date_elem.get_text())
                        published_date = self._parse_naver_date(date_text)
                    
                    # 기사 요약 (검색 결과에서 제공되는 요약)
                    summary_elem = item.find('div', class_='news_dsc')
                    summary = self.clean_text(summary_elem.get_text()) if summary_elem else ""
                    
                    article = NewsArticle(
                        title=title,
                        content=summary,  # 검색 결과에서는 요약만 제공
                        url=url,
                        author=author,
                        published_date=published_date,
                        source=self.source,
                        summary=summary
                    )
                    
                    if self.validate_article_basic(article):
                        articles.append(article)
                
                except Exception as e:
                    logger.warning(f"검색 결과 항목 파싱 오류: {e}")
                    continue
            
            return articles
            
        except Exception as e:
            logger.error(f"검색 결과 파싱 오류: {e}")
            return []
    
    def validate_article_basic(self, article: NewsArticle) -> bool:
        """기본 기사 유효성 검증 (검색 결과용)"""
        if not article.title or len(article.title.strip()) < 5:
            return False
        
        if not article.url or not self.is_valid_url(article.url):
            return False
        
        return True
    
    async def parse_article_detail(self, url: str) -> Optional[NewsArticle]:
        """기사 상세 내용 파싱"""
        try:
            # 네이버 뉴스 URL인지 확인
            if 'news.naver.com' not in url:
                return None
            
            html = await self.fetch_page(url)
            if not html:
                return None
            
            soup = BeautifulSoup(html, 'html.parser')
            
            # 제목 추출
            title_elem = soup.find('h2', class_='media_end_head_headline') or \
                        soup.find('h3', class_='tts_head') or \
                        soup.find('h2', id='title')
            
            if not title_elem:
                logger.warning(f"제목을 찾을 수 없습니다: {url}")
                return None
            
            title = self.clean_text(title_elem.get_text())
            
            # 본문 추출
            content_elem = soup.find('div', class_='newsct_article _article_body') or \
                          soup.find('div', id='newsct_article') or \
                          soup.find('div', class_='_article_body_contents')
            
            if not content_elem:
                logger.warning(f"본문을 찾을 수 없습니다: {url}")
                return None
            
            # 본문에서 불필요한 요소 제거
            for elem in content_elem.find_all(['script', 'style', 'div', 'span']):
                if 'ad' in elem.get('class', []) or 'advertisement' in elem.get('class', []):
                    elem.decompose()
            
            content = self.clean_text(content_elem.get_text())
            
            # 기자 정보 추출
            author_elem = soup.find('em', class_='media_end_head_journalist_name') or \
                         soup.find('span', class_='byline_s') or \
                         soup.find('span', class_='reporter')
            
            author = self.clean_text(author_elem.get_text()) if author_elem else None
            
            # 발행 시간 추출
            date_elem = soup.find('span', class_='media_end_head_info_datestamp_time _ARTICLE_DATE_TIME') or \
                       soup.find('span', class_='t11') or \
                       soup.find('span', class_='date')
            
            published_date = None
            if date_elem:
                date_text = date_elem.get('data-date-time') or date_elem.get_text()
                published_date = self._parse_naver_date(date_text)
            
            # 키워드 추출
            keywords = self.extract_keywords(title, content)
            
            # 요약 생성
            summary = self.generate_summary(content)
            
            article = NewsArticle(
                title=title,
                content=content,
                url=url,
                author=author,
                published_date=published_date,
                source=self.source,
                keywords=keywords,
                summary=summary
            )
            
            if self.validate_article(article):
                return article
            else:
                logger.warning(f"기사 유효성 검증 실패: {url}")
                return None
                
        except Exception as e:
            logger.error(f"기사 상세 파싱 오류 ({url}): {e}")
            return None
    
    def _parse_naver_date(self, date_text: str) -> Optional[datetime]:
        """네이버 날짜 형식 파싱"""
        if not date_text:
            return None
        
        try:
            # 네이버 특화 날짜 형식들
            naver_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y.%m.%d. %H:%M',
                '%Y.%m.%d %H:%M',
                '%Y.%m.%d.',
                '%Y.%m.%d',
            ]
            
            # 상대 시간 처리 ("1시간 전", "2일 전" 등)
            if '전' in date_text:
                return self._parse_relative_time(date_text)
            
            # 절대 시간 처리
            for fmt in naver_formats:
                try:
                    return datetime.strptime(date_text.strip(), fmt)
                except ValueError:
                    continue
            
            # 기본 날짜 파싱 시도
            return self.normalize_date(date_text)
            
        except Exception as e:
            logger.warning(f"네이버 날짜 파싱 실패: {date_text} - {e}")
            return None
    
    def _parse_relative_time(self, time_text: str) -> Optional[datetime]:
        """상대 시간 파싱 ("1시간 전", "2일 전" 등)"""
        try:
            now = datetime.now()
            
            # 숫자 추출
            numbers = re.findall(r'\d+', time_text)
            if not numbers:
                return now
            
            value = int(numbers[0])
            
            if '분' in time_text:
                return now - timedelta(minutes=value)
            elif '시간' in time_text:
                return now - timedelta(hours=value)
            elif '일' in time_text:
                return now - timedelta(days=value)
            elif '주' in time_text:
                return now - timedelta(weeks=value)
            elif '개월' in time_text or '달' in time_text:
                return now - timedelta(days=value * 30)
            else:
                return now
                
        except Exception as e:
            logger.warning(f"상대 시간 파싱 실패: {time_text} - {e}")
            return datetime.now()