import requests
import asyncio
from bs4 import BeautifulSoup
# from newspaper import Article  # Disabled temporarily due to build issues
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import quote_plus, urljoin, urlparse, parse_qs
import re
import logging
import time
import base64
from app.models.schemas import NewsItem, NewsCategory
from app.core.utils import clean_text
from config.settings import settings

# Try to import playwright for advanced scraping
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not available. Install with: pip install playwright")

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseScraper:
    """Base class for all news scrapers."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    async def search(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search for news articles. Must be implemented by subclasses."""
        raise NotImplementedError
    
    def _make_request(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """Make a safe HTTP request with error handling."""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return None


class GoogleSearchScraper(BaseScraper):
    """Scraper for Google Search (priority scraper)."""
    
    def __init__(self):
        super().__init__("Google Search")
        self.base_url = "https://www.google.com/search"
        # More realistic browser headers
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Linux"'
        })
    
    async def search(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """
        Search for news articles using Google Search with Playwright to bypass anti-bot detection.
        
        Args:
            query: Search query
            category: News category (optional)
            limit: Maximum number of results to return
            
        Returns:
            List[NewsItem]: List of news items found
        """
        try:
            # Try Playwright first for better anti-bot evasion
            if PLAYWRIGHT_AVAILABLE:
                return await self._search_google_with_playwright(query, category, limit)
            else:
                # Fallback to DuckDuckGo search
                logger.warning("Playwright not available, falling back to DuckDuckGo")
                return await self._search_duckduckgo(query, category, limit)
            
        except Exception as e:
            logger.error(f"Error in Google Search scraper: {str(e)}")
            return []
    
    
    async def _search_google_with_playwright(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search Google using Playwright for better anti-bot evasion."""
        try:
            # Build search query with news filter
            search_query = f"{query} news"
            if category:
                search_query = f"{query} {category.value} news"
            
            logger.info(f"Searching Google with Playwright for: {search_query}")
            
            async with async_playwright() as p:
                # Launch browser with stealth settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-gpu',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ]
                )
                
                # Create context with additional stealth settings
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US',
                    timezone_id='America/New_York'
                )
                
                # Add stealth scripts
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                    
                    Object.defineProperty(navigator, 'plugins', {
                        get: () => [1, 2, 3, 4, 5],
                    });
                    
                    Object.defineProperty(navigator, 'languages', {
                        get: () => ['en-US', 'en'],
                    });
                    
                    window.chrome = {
                        runtime: {},
                    };
                """)
                
                page = await context.new_page()
                
                # Navigate to Google with news search
                google_url = f"https://www.google.com/search?q={quote_plus(search_query)}&tbm=nws&num={min(limit, 20)}"
                
                try:
                    await page.goto(google_url, wait_until='networkidle', timeout=30000)
                    
                    # Wait for search results to load - try multiple selectors
                    selectors_to_wait = [
                        'div.g',           # Standard Google result container
                        'div.MjjYud',      # Alternative Google container  
                        'div[data-ved]',   # Data-ved containers
                        'h3',              # Title elements
                        '.rc'              # Result container class
                    ]
                    
                    page_loaded = False
                    for selector in selectors_to_wait:
                        try:
                            await page.wait_for_selector(selector, timeout=5000)
                            logger.info(f"Page loaded with selector: {selector}")
                            page_loaded = True
                            break
                        except:
                            continue
                    
                    if not page_loaded:
                        logger.warning("No expected selectors found, proceeding anyway")
                    
                    # Get page content
                    html_content = await page.content()
                    
                except Exception as e:
                    logger.error(f"Failed to load Google search page: {str(e)}")
                    await browser.close()
                    return []
                
                await browser.close()
                
                # Parse results with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find news results
                news_items = []
                scraped_timestamp = datetime.utcnow()
                
                # Google News result selectors
                selectors_to_try = [
                    'div.g h3',          # Standard news results
                    'div.MjjYud h3',     # Alternative Google selector
                    'div[data-ved] h3',  # Data-ved containers with titles
                    'article h3',        # Article containers
                    'div[role="article"] h3',  # Role-based selector
                    '.rc h3',            # Result container with title
                    'h3 a',              # Direct title links
                    'div.yuRUbf h3'      # Another Google selector
                ]
                
                results = []
                for selector in selectors_to_try:
                    results = soup.select(selector)
                    if results:
                        logger.info(f"Found {len(results)} Google results using selector: {selector}")
                        break
                
                for result in results[:limit]:
                    try:
                        news_item = self._parse_google_result(result, scraped_timestamp)
                        if news_item:
                            news_items.append(news_item)
                    except Exception as e:
                        logger.error(f"Error parsing Google result: {str(e)}")
                        continue
                
                logger.info(f"Found {len(news_items)} valid articles from Google Search")
                return news_items
                
        except Exception as e:
            logger.error(f"Error searching Google with Playwright: {str(e)}")
            # Fallback to DuckDuckGo if Playwright fails
            return await self._search_duckduckgo(query, category, limit)
    
    def _parse_google_result(self, result, scraped_timestamp: datetime) -> Optional[NewsItem]:
        """Parse a single Google search result into a NewsItem."""
        try:
            # Find the parent container
            parent = result.find_parent()
            if not parent:
                return None
            
            # Get title
            title = clean_text(result.get_text())
            if not title or len(title) < 10:
                return None
            
            # Find link - look for 'a' tag in various locations
            link_elem = result.find('a') or parent.find('a')
            if not link_elem:
                return None
            
            link = link_elem.get('href', '')
            if not link:
                return None
            
            # Clean Google redirect URLs
            if link.startswith('/url?'):
                try:
                    parsed = urlparse(link)
                    params = parse_qs(parsed.query)
                    if 'url' in params:
                        link = params['url'][0]
                except:
                    pass
            
            # Make relative URLs absolute
            if link.startswith('/'):
                link = f"https://www.google.com{link}"
            
            # Find snippet/description in parent containers
            snippet = "No description available"
            snippet_selectors = [
                '.VwiC3b',      # Google snippet class
                '.s3v9rd',      # Alternative snippet class
                '.IsZvec',      # Another snippet class
                'span[data-ved]', # Data-ved spans often contain snippets
                'div[data-ved] span'  # Nested spans
            ]
            
            for selector in snippet_selectors:
                snippet_elem = parent.select_one(selector)
                if snippet_elem:
                    potential_snippet = clean_text(snippet_elem.get_text())
                    if potential_snippet and len(potential_snippet) > 20:
                        snippet = potential_snippet
                        break
            
            return NewsItem(
                title=title,
                link=link,
                source_name=self.source_name,
                snippet=snippet[:500],
                published_date=None,  # Google doesn't always provide clear dates
                scraped_timestamp=scraped_timestamp
            )
            
        except Exception as e:
            logger.error(f"Error parsing Google result: {str(e)}")
            return None

    async def _search_duckduckgo(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search using DuckDuckGo as a Google alternative."""
        try:
            # Build search query
            search_query = f"{query} news"
            if category:
                search_query = f"{query} {category.value} news"
            
            # Use DuckDuckGo HTML search
            ddg_url = "https://html.duckduckgo.com/html/"
            params = {
                'q': search_query,
                's': '0',  # Start from first result
                'dc': '50',  # Number of results
                'v': 'l',   # Layout
                'o': 'json',
                'api': '/d.js'
            }
            
            logger.info(f"Searching DuckDuckGo for: {search_query}")
            
            # Add some delay to avoid rate limiting
            await asyncio.sleep(0.5)
            
            try:
                # Make request
                response = self.session.get(ddg_url, params=params, timeout=15)
                
                if response.status_code != 200:
                    logger.error(f"DuckDuckGo returned status code: {response.status_code}")
                    return []
                    
            except Exception as e:
                logger.error(f"Request to DuckDuckGo failed: {str(e)}")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find search results
            result_selectors = [
                'div.result',
                'div.web-result',
                'div.result__body',
                'div[class*="result"]'
            ]
            
            results = []
            for selector in result_selectors:
                results = soup.select(selector)
                if results:
                    logger.info(f"Found {len(results)} results using selector: {selector}")
                    break
            
            if not results:
                logger.warning("No search results found in DuckDuckGo response")
                return []
            
            news_items = []
            scraped_timestamp = datetime.utcnow()
            
            for result in results[:limit]:
                try:
                    news_item = self._parse_ddg_result(result, scraped_timestamp)
                    if news_item:
                        news_items.append(news_item)
                except Exception as e:
                    logger.error(f"Error parsing DuckDuckGo result: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} valid articles from DuckDuckGo")
            return news_items
            
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {str(e)}")
            return []
    
    def _parse_ddg_result(self, result, scraped_timestamp: datetime) -> Optional[NewsItem]:
        """Parse a single DuckDuckGo search result into a NewsItem."""
        try:
            # Find title and link
            title_elem = result.select_one('a.result__a') or result.select_one('h2 a') or result.select_one('a')
            
            if not title_elem:
                return None
            
            title = clean_text(title_elem.get_text())
            if not title or len(title) < 10:
                return None
            
            link = title_elem.get('href', '')
            if not link or not link.startswith('http'):
                return None
            
            # Find snippet/description
            snippet_selectors = [
                '.result__snippet',
                '.result__body',
                'a + div',
                'div.snippet'
            ]
            
            snippet = "No description available"
            for selector in snippet_selectors:
                snippet_elem = result.select_one(selector)
                if snippet_elem:
                    potential_snippet = clean_text(snippet_elem.get_text())
                    if potential_snippet and len(potential_snippet) > 20:
                        snippet = potential_snippet
                        break
            
            return NewsItem(
                title=title,
                link=link,
                source_name=self.source_name,
                snippet=snippet[:500],
                published_date=None,  # DuckDuckGo doesn't provide dates easily
                scraped_timestamp=scraped_timestamp
            )
            
        except Exception as e:
            logger.error(f"Error parsing DuckDuckGo result: {str(e)}")
            return None
    
    def _parse_relative_date(self, date_text: str) -> Optional[datetime]:
        """Parse relative dates like '2 hours ago' into datetime."""
        try:
            from datetime import timedelta
            
            now = datetime.utcnow()
            
            # Extract number and unit
            match = re.search(r'(\d+)\s*(minute|hour|day|week)s?\s*ago', date_text.lower())
            if not match:
                return None
            
            amount, unit = match.groups()
            amount = int(amount)
            
            if unit == 'minute':
                return now - timedelta(minutes=amount)
            elif unit == 'hour':
                return now - timedelta(hours=amount)
            elif unit == 'day':
                return now - timedelta(days=amount)
            elif unit == 'week':
                return now - timedelta(weeks=amount)
            
            return None
        except:
            return None


class GoogleNewsScraper(BaseScraper):
    """Scraper for Google News."""
    
    def __init__(self):
        super().__init__("Google News")
        self.base_url = "https://news.google.com/rss/search"
    
    async def search(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """
        Search Google News for articles using Playwright and RSS feeds.
        
        Args:
            query: Search query
            category: News category (optional)
            limit: Maximum number of results to return
            
        Returns:
            List[NewsItem]: List of news items found
        """
        try:
            # Try RSS feed first (more reliable)
            results = await self._search_google_news_rss(query, category, limit)
            
            if not results and PLAYWRIGHT_AVAILABLE:
                # Fallback to web scraping with Playwright
                logger.info("RSS failed, trying Google News with Playwright")
                results = await self._search_google_news_with_playwright(query, category, limit)
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching Google News: {str(e)}")
            return []
    
    async def _search_google_news_rss(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search Google News using RSS feed."""
        try:
            # Build search URL
            search_query = query
            if category:
                search_query = f"{query} {category.value}"
            
            encoded_query = quote_plus(search_query)
            search_url = f"{self.base_url}?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            logger.info(f"Searching Google News RSS: {search_url}")
            
            # Make request
            response = self._make_request(search_url)
            if not response:
                return []
            
            # Parse RSS feed
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            news_items = []
            scraped_timestamp = datetime.utcnow()
            
            for item in items[:limit]:
                try:
                    news_item = self._parse_rss_item(item, scraped_timestamp)
                    if news_item:
                        news_items.append(news_item)
                except Exception as e:
                    logger.error(f"Error parsing RSS item: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} articles from Google News RSS")
            return news_items
            
        except Exception as e:
            logger.error(f"Error searching Google News RSS: {str(e)}")
            return []
    
    async def _search_google_news_with_playwright(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search Google News using Playwright for better results."""
        try:
            # Build search query
            search_query = query
            if category:
                search_query = f"{query} {category.value}"
            
            logger.info(f"Searching Google News with Playwright for: {search_query}")
            
            async with async_playwright() as p:
                # Launch browser with stealth settings
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-dev-shm-usage',
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-gpu',
                        '--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                    ]
                )
                
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    locale='en-US'
                )
                
                # Add stealth scripts
                await context.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined,
                    });
                """)
                
                page = await context.new_page()
                
                # Navigate to Google News
                news_url = f"https://news.google.com/search?q={quote_plus(search_query)}&hl=en-US&gl=US&ceid=US:en"
                
                try:
                    await page.goto(news_url, wait_until='networkidle', timeout=30000)
                    
                    # Wait for articles to load
                    await page.wait_for_selector('article', timeout=15000)
                    
                    # Get page content
                    html_content = await page.content()
                    
                except Exception as e:
                    logger.error(f"Failed to load Google News page: {str(e)}")
                    await browser.close()
                    return []
                
                await browser.close()
                
                # Parse results with BeautifulSoup
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # Find news articles
                news_items = []
                scraped_timestamp = datetime.utcnow()
                
                # Google News article selectors
                articles = soup.find_all('article') or soup.select('div[data-n-tid]')
                
                for article in articles[:limit]:
                    try:
                        news_item = self._parse_google_news_article(article, scraped_timestamp)
                        if news_item:
                            news_items.append(news_item)
                    except Exception as e:
                        logger.error(f"Error parsing Google News article: {str(e)}")
                        continue
                
                logger.info(f"Found {len(news_items)} articles from Google News Playwright")
                return news_items
                
        except Exception as e:
            logger.error(f"Error searching Google News with Playwright: {str(e)}")
            return []
    
    def _parse_google_news_article(self, article, scraped_timestamp: datetime) -> Optional[NewsItem]:
        """Parse a single Google News article into a NewsItem."""
        try:
            # Find title
            title_selectors = ['h3', 'h4', 'a[aria-label]', '.JtKRv']
            title_elem = None
            
            for selector in title_selectors:
                title_elem = article.select_one(selector)
                if title_elem:
                    break
            
            if not title_elem:
                return None
            
            title = clean_text(title_elem.get_text())
            if not title or len(title) < 10:
                return None
            
            # Find link
            link_elem = article.find('a') or title_elem.find('a') if hasattr(title_elem, 'find') else None
            if not link_elem:
                return None
            
            link = link_elem.get('href', '')
            if not link:
                return None
            
            # Handle relative URLs
            if link.startswith('./'):
                link = f"https://news.google.com{link[1:]}"
            elif link.startswith('/'):
                link = f"https://news.google.com{link}"
            
            # Try to extract original URL if it's a Google News redirect
            if 'news.google.com' in link and '/articles/' in link:
                # For now, just mark as Google News link since async extraction needs refactoring
                snippet = f"[Google News Link] {snippet}" if snippet != "No description available" else "[Google News Link]"
            
            # Find snippet
            snippet_selectors = ['.GI74Re', '.LEwnzc', 'div[data-n-tid] div']
            snippet = "No description available"
            
            for selector in snippet_selectors:
                snippet_elem = article.select_one(selector)
                if snippet_elem:
                    potential_snippet = clean_text(snippet_elem.get_text())
                    if potential_snippet and len(potential_snippet) > 20:
                        snippet = potential_snippet
                        break
            
            return NewsItem(
                title=title,
                link=link,
                source_name=self.source_name,
                snippet=snippet[:500],
                published_date=None,  # Would need additional parsing for dates
                scraped_timestamp=scraped_timestamp
            )
            
        except Exception as e:
            logger.error(f"Error parsing Google News article: {str(e)}")
            return None
    
    async def _extract_original_url_with_playwright(self, google_news_url: str) -> str:
        """Extract original URL using Playwright to handle redirects."""
        if not PLAYWRIGHT_AVAILABLE:
            return google_news_url
            
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()
                
                # Set up request interception to catch redirects
                final_url = google_news_url
                
                async def handle_response(response):
                    nonlocal final_url
                    if response.status in [301, 302, 303, 307, 308]:
                        location = response.headers.get('location')
                        if location and 'google.com' not in location:
                            final_url = location
                    elif response.status == 200 and 'google.com' not in response.url:
                        final_url = response.url
                
                page.on('response', handle_response)
                
                try:
                    await page.goto(google_news_url, timeout=10000, wait_until='domcontentloaded')
                    await page.wait_for_timeout(2000)  # Wait for any redirects
                    
                    # Check if we ended up on a different domain
                    current_url = page.url
                    if current_url != google_news_url and 'google.com' not in current_url:
                        final_url = current_url
                        
                except Exception:
                    pass  # Ignore timeout errors, use what we have
                
                await browser.close()
                
                if final_url != google_news_url:
                    logger.info(f"Successfully extracted original URL: {final_url}")
                    return final_url
                
        except Exception as e:
            logger.debug(f"Playwright URL extraction failed: {str(e)}")
        
        return google_news_url
    
    def _extract_original_url_from_google_news(self, google_news_url: str) -> str:
        """Extract the original article URL from Google News redirect URL by actually following it."""
        try:
            logger.info(f"Attempting to extract URL from: {google_news_url[:100]}...")
            
            # Method 1: Follow multiple redirects with session that handles cookies
            try:
                # Create a new session for this request to avoid conflicts
                redirect_session = requests.Session()
                redirect_session.headers.update({
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.9',
                    'Accept-Encoding': 'gzip, deflate, br',
                    'Connection': 'keep-alive',
                    'Upgrade-Insecure-Requests': '1',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'cross-site',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                })
                
                # Follow redirects manually with multiple attempts
                current_url = google_news_url
                max_redirects = 10
                redirect_count = 0
                
                while redirect_count < max_redirects:
                    response = redirect_session.get(
                        current_url,
                        timeout=15,
                        allow_redirects=False,  # Handle redirects manually
                        stream=False
                    )
                    
                    # Check if we got a redirect
                    if response.status_code in [301, 302, 303, 307, 308]:
                        location = response.headers.get('Location')
                        if location:
                            if location.startswith('/'):
                                # Relative URL, make it absolute
                                from urllib.parse import urljoin
                                current_url = urljoin(current_url, location)
                            else:
                                current_url = location
                            
                            logger.debug(f"Redirect {redirect_count + 1}: {current_url[:100]}...")
                            
                            # Check if we've reached a non-Google URL
                            if not any(domain in current_url for domain in ['google.com', 'googleusercontent.com', 'gstatic.com']):
                                logger.info(f"Successfully extracted URL via redirect: {current_url}")
                                return current_url
                            
                            redirect_count += 1
                            continue
                    
                    elif response.status_code == 200:
                        # Check if this is the final URL and it's different from the original
                        if current_url != google_news_url and not any(domain in current_url for domain in ['google.com', 'googleusercontent.com']):
                            logger.info(f"Final URL reached: {current_url}")
                            return current_url
                        
                        # Check the response content for redirects or the actual URL
                        content = response.text.lower()
                        
                        # Look for meta refresh tags
                        import re
                        meta_refresh = re.search(r'<meta[^>]*http-equiv=["\']?refresh["\']?[^>]*content=["\']?\d+;\s*url=([^"\'>\s]+)', content, re.IGNORECASE)
                        if meta_refresh:
                            refresh_url = meta_refresh.group(1)
                            if refresh_url.startswith('http') and 'google.com' not in refresh_url:
                                logger.info(f"Found meta refresh URL: {refresh_url}")
                                return refresh_url
                        
                        # Look for canonical URLs
                        canonical = re.search(r'<link[^>]*rel=["\']?canonical["\']?[^>]*href=["\']?([^"\'>\s]+)', content, re.IGNORECASE)
                        if canonical:
                            canonical_url = canonical.group(1)
                            if canonical_url.startswith('http') and 'google.com' not in canonical_url:
                                logger.info(f"Found canonical URL: {canonical_url}")
                                return canonical_url
                        
                        # Look for Open Graph URL
                        og_url = re.search(r'<meta[^>]*property=["\']?og:url["\']?[^>]*content=["\']?([^"\'>\s]+)', content, re.IGNORECASE)
                        if og_url:
                            og_url_value = og_url.group(1)
                            if og_url_value.startswith('http') and 'google.com' not in og_url_value:
                                logger.info(f"Found OG URL: {og_url_value}")
                                return og_url_value
                        
                        # Look for window.location redirects in JavaScript
                        js_redirect = re.search(r'window\.location(?:\.href)?\s*=\s*["\']([^"\']+)["\']', content, re.IGNORECASE)
                        if js_redirect:
                            js_url = js_redirect.group(1)
                            if js_url.startswith('http') and 'google.com' not in js_url:
                                logger.info(f"Found JS redirect URL: {js_url}")
                                return js_url
                        
                        break
                    
                    else:
                        logger.warning(f"Got status code {response.status_code} for URL: {current_url}")
                        break
                
                redirect_session.close()
                        
            except Exception as e:
                logger.debug(f"Advanced redirect method failed: {str(e)}")
            
            # Method 2: Try to decode the Google News article ID
            if 'articles/' in google_news_url:
                try:
                    # Extract the encoded part after /articles/
                    encoded_part = google_news_url.split('articles/')[-1]
                    encoded_part = encoded_part.split('?')[0]  # Remove query params
                    
                    # Google News uses a custom encoding, try different decoding approaches
                    import base64
                    
                    # Try standard base64 decoding with padding
                    for padding in ['', '=', '==', '===']:
                        try:
                            padded = encoded_part + padding
                            decoded_bytes = base64.b64decode(padded, validate=False)
                            decoded = decoded_bytes.decode('utf-8', errors='ignore')
                            
                            # Look for URL patterns in decoded string
                            url_patterns = [
                                r'https?://(?!.*google\.com)[^\s<>"\'\\]+',
                                r'www\.(?!google)[^\s<>"\'\\]+',
                                r'[a-zA-Z0-9.-]+\.(?:com|org|net|edu|gov|co\.uk|de|fr|it|es|ru|cn|jp|au|ca)[^\s<>"\'\\]*',
                            ]
                            
                            for pattern in url_patterns:
                                matches = re.findall(pattern, decoded)
                                for match in matches:
                                    if not match.startswith('http'):
                                        match = 'https://' + match
                                    if len(match) > 20 and 'google.com' not in match:
                                        logger.info(f"Decoded URL found: {match}")
                                        # Validate the URL by making a quick HEAD request
                                        try:
                                            head_response = requests.head(match, timeout=5)
                                            if head_response.status_code < 400:
                                                return match
                                        except:
                                            continue
                                        
                        except Exception:
                            continue
                            
                except Exception as e:
                    logger.debug(f"Base64 decoding failed: {str(e)}")
            
            # Method 3: Try to parse URL parameters for embedded URLs
            try:
                parsed = urlparse(google_news_url)
                query_params = parse_qs(parsed.query)
                
                # Check common URL parameter names
                for param in ['url', 'u', 'link', 'q', 'target', 'dest']:
                    if param in query_params:
                        potential_url = query_params[param][0]
                        if potential_url.startswith('http') and 'google.com' not in potential_url:
                            logger.info(f"Found URL in parameters: {potential_url}")
                            return potential_url
                            
            except Exception as e:
                logger.debug(f"URL parameter parsing failed: {str(e)}")
            
            # Method 4: Try to extract domain from article ID and make a reasonable guess
            if google_news_url.startswith('https://news.google.com/articles/'):
                try:
                    article_id = google_news_url.split('articles/')[-1].split('?')[0]
                    
                    # Try to match known news site patterns in the article ID
                    site_patterns = {
                        'reuters': 'reuters.com',
                        'bbc': 'bbc.com', 
                        'cnn': 'cnn.com',
                        'bloomberg': 'bloomberg.com',
                        'techcrunch': 'techcrunch.com',
                        'wsj': 'wsj.com',
                        'nytimes': 'nytimes.com',
                        'ap': 'apnews.com',
                        'guardian': 'theguardian.com',
                        'washingtonpost': 'washingtonpost.com',
                        'forbes': 'forbes.com',
                        'cnbc': 'cnbc.com'
                    }
                    
                    for site_key, domain in site_patterns.items():
                        if site_key.lower() in article_id.lower():
                            logger.info(f"Detected {domain} article from ID pattern")
                            return f"https://{domain}"  # Return domain as fallback
                            
                except Exception as e:
                    logger.debug(f"Article ID parsing failed: {str(e)}")
            
            # If all methods fail, return original URL
            logger.warning(f"Could not extract original URL from: {google_news_url[:100]}...")
            return google_news_url
            
        except Exception as e:
            logger.error(f"Error extracting original URL: {str(e)}")
            return google_news_url

    def _parse_rss_item(self, item, scraped_timestamp: datetime) -> Optional[NewsItem]:
        """Parse a single RSS item into a NewsItem."""
        try:
            title_elem = item.find('title')
            link_elem = item.find('link')
            description_elem = item.find('description')
            pub_date_elem = item.find('pubDate')
            
            if not title_elem or not link_elem:
                return None
            
            title = clean_text(title_elem.get_text())
            link = link_elem.get_text().strip()
            
            # Initialize snippet first
            snippet = ""
            if description_elem:
                # Parse HTML in description
                desc_soup = BeautifulSoup(description_elem.get_text(), 'html.parser')
                snippet = clean_text(desc_soup.get_text())
            
            # Extract actual URL from Google News redirect
            if 'news.google.com' in link:
                original_link = self._extract_original_url_from_google_news(link)
                if original_link != link:
                    link = original_link
                else:
                    # If extraction failed, add a note to the snippet
                    snippet = f"[Google News Link - Original URL not extracted] {snippet}" if snippet else "[Google News Link - Original URL not extracted]"
            
            # Parse publication date
            published_date = None
            if pub_date_elem:
                try:
                    pub_date_str = pub_date_elem.get_text()
                    published_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                except:
                    try:
                        # Try alternative format
                        published_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %z')
                    except:
                        logger.warning(f"Could not parse date: {pub_date_str}")
            
            return NewsItem(
                title=title,
                link=link,
                source_name=self.source_name,
                snippet=snippet[:500] if snippet else "No description available",
                published_date=published_date,
                scraped_timestamp=scraped_timestamp
            )
            
        except Exception as e:
            logger.error(f"Error parsing RSS item: {str(e)}")
            return None


class BingNewsScraper(BaseScraper):
    """Scraper for Bing News."""
    
    def __init__(self):
        super().__init__("Bing News")
        self.base_url = "https://www.bing.com/news/search"
    
    async def search(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """
        Search Bing News for articles.
        
        Args:
            query: Search query
            category: News category (optional)
            limit: Maximum number of results to return
            
        Returns:
            List[NewsItem]: List of news items found
        """
        try:
            # Build search query
            search_query = query
            if category:
                search_query = f"{query} {category.value}"
            
            # Build URL with proper parameters
            params = {
                'q': search_query,
                'qft': 'interval="7"',  # Last 7 days - fixed format
                'form': 'HDRSC1',  # Different form value
                'count': min(limit, 20),
                'offset': 0
            }
            
            # Construct URL manually
            param_string = '&'.join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
            search_url = f"{self.base_url}?{param_string}"
            
            logger.info(f"Searching Bing News: {search_url}")
            
            # Make request with proper headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Referer': 'https://www.bing.com/',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = self.session.get(search_url, headers=headers, timeout=15)
            if not response or response.status_code != 200:
                logger.error(f"Failed to get Bing response: {response.status_code if response else 'No response'}")
                return []
            
            # Parse HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try multiple selectors for news cards
            selectors_to_try = [
                'div.news-card',
                'div.newsitem',
                'div[data-eventpayload]',
                'div.newsCardContainer',
                'div.newsCardBody',
                'div.news-card-body',
                'div.b_ans',
                'div.b_algo',
                'li.b_algo',
                'article',
                'div[id*="news"]'
            ]
            
            news_cards = []
            for selector in selectors_to_try:
                news_cards = soup.select(selector)
                if news_cards:
                    logger.info(f"Found {len(news_cards)} results using selector: {selector}")
                    break
            
            if not news_cards:
                # Fallback: look for any div with news-related classes or links
                news_cards = soup.find_all('div', class_=re.compile(r'news|card|item'))
                if not news_cards:
                    # Last resort: find all divs with links
                    news_cards = soup.find_all('div', recursive=True)
                    news_cards = [card for card in news_cards if card.find('a')]
                
                logger.info(f"Fallback found {len(news_cards)} potential news items")
            
            news_items = []
            scraped_timestamp = datetime.utcnow()
            
            for card in news_cards[:limit]:
                try:
                    news_item = self._parse_news_card(card, scraped_timestamp)
                    if news_item:
                        news_items.append(news_item)
                except Exception as e:
                    logger.error(f"Error parsing news card: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} articles from Bing News")
            return news_items
            
        except Exception as e:
            logger.error(f"Error searching Bing News: {str(e)}")
            return []
    
    def _parse_news_card(self, card, scraped_timestamp: datetime) -> Optional[NewsItem]:
        """Parse a single news card into a NewsItem."""
        try:
            # Try multiple selectors for title and link
            title_selectors = [
                'a.title',
                'h3 a',
                'h2 a', 
                'h4 a',
                'a[href*="news"]',
                'a[href*="http"]',
                '.b_topTitle a',
                '.b_title a',
                'cite + a',
                'a'
            ]
            
            title_elem = None
            link = None
            
            for selector in title_selectors:
                title_elem = card.select_one(selector)
                if title_elem:
                    link = title_elem.get('href', '')
                    if link and ('http' in link or link.startswith('/')):
                        break
            
            if not title_elem:
                return None
            
            title = clean_text(title_elem.get_text())
            if not title:
                return None
            
            # Clean up the link
            if link.startswith('/'):
                link = urljoin('https://www.bing.com', link)
            elif not link.startswith('http'):
                return None
            
            # Try multiple selectors for snippet/description
            snippet_selectors = [
                '.snippet',
                '.b_caption p',
                '.b_snippet',
                'p',
                '.news-card-body p',
                'div[class*="caption"]',
                'div[class*="snippet"]'
            ]
            
            snippet = "No description available"
            for selector in snippet_selectors:
                snippet_elem = card.select_one(selector)
                if snippet_elem:
                    potential_snippet = clean_text(snippet_elem.get_text())
                    if potential_snippet and len(potential_snippet) > 20:  # Ensure it's substantial
                        snippet = potential_snippet
                        break
            
            # Try to find publication date
            published_date = None
            date_selectors = [
                '.timestamp',
                'time',
                '.b_attribution',
                'span[class*="time"]',
                'span[class*="date"]',
                '.news-source-datetime'
            ]
            
            for selector in date_selectors:
                date_elem = card.select_one(selector)
                if date_elem:
                    try:
                        date_text = date_elem.get_text()
                        # Try to parse relative dates like "2 hours ago"
                        if 'ago' in date_text.lower():
                            published_date = self._parse_relative_date(date_text)
                        else:
                            # Try absolute date parsing
                            published_date = datetime.strptime(date_text.strip(), '%Y-%m-%d')
                        break
                    except:
                        continue
            
            return NewsItem(
                title=title,
                link=link,
                source_name=self.source_name,
                snippet=snippet[:500],
                published_date=published_date,
                scraped_timestamp=scraped_timestamp
            )
            
        except Exception as e:
            logger.error(f"Error parsing news card: {str(e)}")
            return None
    
    def _parse_relative_date(self, date_text: str) -> Optional[datetime]:
        """Parse relative dates like '2 hours ago' into datetime."""
        try:
            import re
            from datetime import timedelta
            
            now = datetime.utcnow()
            
            # Extract number and unit
            match = re.search(r'(\d+)\s*(minute|hour|day|week)s?\s*ago', date_text.lower())
            if not match:
                return None
            
            amount, unit = match.groups()
            amount = int(amount)
            
            if unit == 'minute':
                return now - timedelta(minutes=amount)
            elif unit == 'hour':
                return now - timedelta(hours=amount)
            elif unit == 'day':
                return now - timedelta(days=amount)
            elif unit == 'week':
                return now - timedelta(weeks=amount)
            
            return None
        except:
            return None


class DuckDuckGoScraper(BaseScraper):
    """Scraper for DuckDuckGo search (Google alternative)."""
    
    def __init__(self):
        super().__init__("DuckDuckGo")
        self.base_url = "https://html.duckduckgo.com/html/"
    
    async def search(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search DuckDuckGo for news articles."""
        try:
            # Build search query
            search_query = f"{query} news"
            if category:
                search_query = f"{query} {category.value} news"
            
            params = {
                'q': search_query,
                's': '0',
                'dc': str(min(limit * 2, 50)),
                'v': 'l',
                'o': 'json',
                'api': '/d.js'
            }
            
            logger.info(f"Searching DuckDuckGo for: {search_query}")
            
            response = self.session.get(self.base_url, params=params, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find search results
            results = soup.select('div.result') or soup.select('div.web-result')
            
            news_items = []
            scraped_timestamp = datetime.utcnow()
            
            for result in results[:limit]:
                try:
                    # Find title and link
                    title_elem = result.select_one('a.result__a') or result.select_one('h2 a') or result.select_one('a')
                    if not title_elem:
                        continue
                    
                    title = clean_text(title_elem.get_text())
                    if not title or len(title) < 10:
                        continue
                    
                    link = title_elem.get('href', '')
                    if not link or not link.startswith('http'):
                        continue
                    
                    # Find snippet
                    snippet_elem = result.select_one('.result__snippet') or result.select_one('a + div')
                    snippet = clean_text(snippet_elem.get_text()) if snippet_elem else "No description available"
                    
                    news_items.append(NewsItem(
                        title=title,
                        link=link,
                        source_name=self.source_name,
                        snippet=snippet[:500],
                        published_date=None,
                        scraped_timestamp=scraped_timestamp
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing DuckDuckGo result: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} articles from DuckDuckGo")
            return news_items
            
        except Exception as e:
            logger.error(f"Error searching DuckDuckGo: {str(e)}")
            return []


class MediumScraper(BaseScraper):
    """Scraper for Medium articles using multiple approaches."""
    
    def __init__(self):
        super().__init__("Medium")
        self.search_url = "https://medium.com/search"
        self.tag_url = "https://medium.com/tag"
        
        # Enhanced headers to look more like a real browser
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0'
        })
    
    async def search(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search Medium for articles using multiple strategies."""
        try:
            # Strategy 1: Try tag-based search first (more reliable)
            tag_results = await self._search_by_tag(query, limit)
            if tag_results:
                return tag_results
            
            # Strategy 2: Try direct search
            search_results = await self._search_direct(query, category, limit)
            if search_results:
                return search_results
                
            # Strategy 3: Try RSS approach for popular topics
            rss_results = await self._search_via_rss(query, limit)
            return rss_results
            
        except Exception as e:
            logger.error(f"Error searching Medium: {str(e)}")
            return []
    
    async def _search_by_tag(self, query: str, limit: int = 10) -> List[NewsItem]:
        """Search Medium by tag (more reliable approach)."""
        try:
            # Convert query to tag format
            tag = query.lower().replace(' ', '-').replace('_', '-')
            tag_candidates = [
                tag,
                query.lower().replace(' ', ''),
                query.split()[0] if ' ' in query else query
            ]
            
            for tag_name in tag_candidates:
                try:
                    url = f"{self.tag_url}/{tag_name}"
                    logger.info(f"Trying Medium tag: {url}")
                    
                    response = self.session.get(url, timeout=15)
                    if response.status_code != 200:
                        continue
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find articles in tag page
                    articles = self._extract_articles_from_soup(soup, limit)
                    if articles:
                        logger.info(f"Found {len(articles)} articles from Medium tag: {tag_name}")
                        return articles
                        
                except Exception as e:
                    logger.debug(f"Failed tag {tag_name}: {str(e)}")
                    continue
            
            return []
            
        except Exception as e:
            logger.error(f"Error in Medium tag search: {str(e)}")
            return []
    
    async def _search_direct(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Direct search on Medium."""
        try:
            search_query = query
            if category:
                search_query = f"{query} {category.value}"
            
            params = {
                'q': search_query
            }
            
            logger.info(f"Searching Medium directly for: {search_query}")
            
            response = self.session.get(self.search_url, params=params, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            return self._extract_articles_from_soup(soup, limit)
            
        except Exception as e:
            logger.error(f"Error in Medium direct search: {str(e)}")
            return []
    
    async def _search_via_rss(self, query: str, limit: int = 10) -> List[NewsItem]:
        """Try to get Medium articles via RSS feeds for popular topics."""
        try:
            # Medium has topic-based RSS feeds
            topic_mappings = {
                'technology': 'tech',
                'programming': 'programming', 
                'python': 'python',
                'javascript': 'javascript',
                'ai': 'artificial-intelligence',
                'machine learning': 'machine-learning',
                'data science': 'data-science',
                'startup': 'entrepreneurship',
                'business': 'business'
            }
            
            query_lower = query.lower()
            topic = None
            
            # Find matching topic
            for key, value in topic_mappings.items():
                if key in query_lower:
                    topic = value
                    break
            
            if not topic:
                return []
            
            rss_url = f"https://medium.com/feed/tag/{topic}"
            logger.info(f"Trying Medium RSS: {rss_url}")
            
            response = self.session.get(rss_url, timeout=15)
            if response.status_code != 200:
                return []
            
            # Parse RSS
            soup = BeautifulSoup(response.content, 'xml')
            items = soup.find_all('item')
            
            news_items = []
            scraped_timestamp = datetime.utcnow()
            
            for item in items[:limit]:
                try:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    description_elem = item.find('description')
                    pub_date_elem = item.find('pubDate')
                    
                    if not title_elem or not link_elem:
                        continue
                    
                    title = clean_text(title_elem.get_text())
                    link = link_elem.get_text().strip()
                    
                    # Clean up description HTML
                    snippet = "No description available"
                    if description_elem:
                        desc_soup = BeautifulSoup(description_elem.get_text(), 'html.parser')
                        snippet = clean_text(desc_soup.get_text())[:500]
                    
                    # Parse publication date
                    published_date = None
                    if pub_date_elem:
                        try:
                            pub_date_str = pub_date_elem.get_text()
                            published_date = datetime.strptime(pub_date_str, '%a, %d %b %Y %H:%M:%S %Z')
                        except:
                            pass
                    
                    news_items.append(NewsItem(
                        title=title,
                        link=link,
                        source_name=self.source_name,
                        snippet=snippet,
                        published_date=published_date,
                        scraped_timestamp=scraped_timestamp
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing Medium RSS item: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} articles from Medium RSS")
            return news_items
            
        except Exception as e:
            logger.error(f"Error in Medium RSS search: {str(e)}")
            return []
    
    def _extract_articles_from_soup(self, soup: BeautifulSoup, limit: int = 10) -> List[NewsItem]:
        """Extract articles from BeautifulSoup object."""
        try:
            # Multiple selectors for Medium articles
            article_selectors = [
                'article[data-testid="story-preview"]',
                'div[data-testid="story-preview"]', 
                'article',
                'div.postArticle',
                'div.u-lineHeightTightest',
                'div[class*="story"]',
                'h1 a[href*="medium.com"]',
                'h2 a[href*="medium.com"]',
                'h3 a[href*="medium.com"]'
            ]
            
            articles = []
            for selector in article_selectors:
                articles = soup.select(selector)
                if articles:
                    logger.debug(f"Found articles using selector: {selector}")
                    break
            
            if not articles:
                # Fallback: look for any links that contain medium.com
                articles = soup.find_all('a', href=lambda x: x and 'medium.com' in x)
            
            news_items = []
            scraped_timestamp = datetime.utcnow()
            seen_links = set()
            
            for article in articles[:limit * 2]:  # Get more to filter duplicates
                try:
                    if len(news_items) >= limit:
                        break
                    
                    # Find title and link
                    if article.name == 'a':
                        title_elem = article
                        link = article.get('href', '')
                    else:
                        title_selectors = [
                            'h1 a', 'h2 a', 'h3 a',
                            'a[data-action="open-post"]',
                            'a[href*="medium.com"]',
                            'h1', 'h2', 'h3'
                        ]
                        
                        title_elem = None
                        link = ""
                        
                        for selector in title_selectors:
                            title_elem = article.select_one(selector)
                            if title_elem:
                                if title_elem.name == 'a':
                                    link = title_elem.get('href', '')
                                else:
                                    # Look for parent link
                                    parent_link = title_elem.find_parent('a')
                                    if parent_link:
                                        link = parent_link.get('href', '')
                                break
                    
                    if not title_elem:
                        continue
                        
                    title = clean_text(title_elem.get_text())
                    if not title or len(title) < 10:
                        continue
                    
                    # Clean up link
                    if link.startswith('/'):
                        link = f"https://medium.com{link}"
                    elif not link.startswith('http'):
                        continue
                    
                    # Remove Medium's tracking parameters
                    if '?' in link:
                        link = link.split('?')[0]
                    
                    # Skip duplicates
                    if link in seen_links:
                        continue
                    seen_links.add(link)
                    
                    # Find snippet
                    snippet_selectors = [
                        'p[data-testid="story-preview-description"]',
                        '.graf--p',
                        'div.postArticle-content p',
                        'p',
                        'div[data-testid*="preview"]'
                    ]
                    snippet = "No description available"
                    
                    snippet_context = article if article.name != 'a' else article.find_parent()
                    if snippet_context:
                        for selector in snippet_selectors:
                            snippet_elem = snippet_context.select_one(selector)
                            if snippet_elem:
                                potential_snippet = clean_text(snippet_elem.get_text())
                                if potential_snippet and len(potential_snippet) > 20:
                                    snippet = potential_snippet
                                    break
                    
                    news_items.append(NewsItem(
                        title=title,
                        link=link,
                        source_name=self.source_name,
                        snippet=snippet[:500],
                        published_date=None,
                        scraped_timestamp=scraped_timestamp
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing Medium article: {str(e)}")
                    continue
            
            return news_items
            
        except Exception as e:
            logger.error(f"Error extracting Medium articles: {str(e)}")
            return []


class DevToScraper(BaseScraper):
    """Scraper for Dev.to articles using API."""
    
    def __init__(self):
        super().__init__("Dev.to")
        self.api_base_url = "https://dev.to/api/articles"
        self.api_key = settings.DEVTO_API_KEY
        self.search_url = "https://dev.to/search"
        
        # Update headers for API
        self.session.headers.update({
            'api-key': self.api_key,
            'Accept': 'application/vnd.forem.api-v1+json'
        })
    
    async def search(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search Dev.to for articles using API first, fallback to scraping."""
        try:
            # First try API approach
            logger.info(f"Searching Dev.to API for: {query}")
            api_results = await self._search_with_api(query, limit)
            
            if api_results:
                return api_results
                
            # Fallback to scraping if API fails
            logger.info("Dev.to API failed, falling back to web scraping")
            return await self._search_with_scraping(query, category, limit)
            
        except Exception as e:
            logger.error(f"Error searching Dev.to: {str(e)}")
            return []
    
    async def _search_with_api(self, query: str, limit: int = 10) -> List[NewsItem]:
        """Search using Dev.to API."""
        try:
            # Search approach 1: Get articles by tag
            tag_results = await self._search_api_by_tag(query, limit)
            if tag_results:
                return tag_results
            
            # Search approach 2: Get recent articles and filter
            recent_results = await self._search_api_recent_filtered(query, limit)
            return recent_results
            
        except Exception as e:
            logger.error(f"Error with Dev.to API: {str(e)}")
            return []
    
    async def _search_api_by_tag(self, query: str, limit: int = 10) -> List[NewsItem]:
        """Search Dev.to API by tag."""
        try:
            # Convert query to potential tags
            potential_tags = [
                query.lower().replace(' ', ''),
                query.lower().replace(' ', '-'),
                query.split()[0].lower() if ' ' in query else query.lower()
            ]
            
            for tag in potential_tags:
                try:
                    params = {
                        'tag': tag,
                        'per_page': min(limit, 30),
                        'state': 'fresh'
                    }
                    
                    response = self.session.get(self.api_base_url, params=params, timeout=15)
                    
                    if response.status_code == 200:
                        articles_data = response.json()
                        if articles_data:
                            logger.info(f"Found {len(articles_data)} articles from Dev.to tag: {tag}")
                            return self._convert_api_results(articles_data, limit)
                            
                except Exception as e:
                    logger.debug(f"Failed Dev.to tag {tag}: {str(e)}")
                    continue
            
            return []
            
        except Exception as e:
            logger.error(f"Error in Dev.to tag search: {str(e)}")
            return []
    
    async def _search_api_recent_filtered(self, query: str, limit: int = 10) -> List[NewsItem]:
        """Get recent articles and filter by query."""
        try:
            # Get recent articles
            params = {
                'per_page': 100,  # Get more to filter
                'state': 'fresh',
                'top': '30'  # Top articles from last 30 days
            }
            
            response = self.session.get(self.api_base_url, params=params, timeout=15)
            
            if response.status_code != 200:
                logger.warning(f"Dev.to API returned status {response.status_code}")
                return []
            
            articles_data = response.json()
            
            # Filter articles by query
            filtered_articles = []
            query_words = query.lower().split()
            
            for article in articles_data:
                title = article.get('title', '').lower()
                description = article.get('description', '').lower()
                tags = ' '.join(article.get('tag_list', [])).lower()
                
                # Calculate relevance score
                score = 0
                for word in query_words:
                    if word in title:
                        score += 3
                    if word in description:
                        score += 2
                    if word in tags:
                        score += 1
                
                if score > 0:
                    filtered_articles.append((article, score))
            
            # Sort by relevance score
            filtered_articles.sort(key=lambda x: x[1], reverse=True)
            
            # Take top results
            top_articles = [article for article, score in filtered_articles[:limit]]
            
            if top_articles:
                logger.info(f"Found {len(top_articles)} relevant articles from Dev.to")
                return self._convert_api_results(top_articles, limit)
            
            return []
            
        except Exception as e:
            logger.error(f"Error filtering Dev.to articles: {str(e)}")
            return []
    
    def _convert_api_results(self, articles_data: list, limit: int = 10) -> List[NewsItem]:
        """Convert API results to NewsItem objects."""
        news_items = []
        scraped_timestamp = datetime.utcnow()
        
        for article in articles_data[:limit]:
            try:
                # Parse published date
                published_date = None
                if article.get('published_at'):
                    try:
                        published_date = datetime.fromisoformat(article['published_at'].replace('Z', '+00:00'))
                    except:
                        pass
                
                # Clean title and description
                title = clean_text(article.get('title', ''))
                description = clean_text(article.get('description', ''))
                
                if not title:
                    continue
                
                news_item = NewsItem(
                    title=title,
                    link=article.get('url', ''),
                    source_name=self.source_name,
                    snippet=description[:500] if description else "No description available",
                    published_date=published_date,
                    scraped_timestamp=scraped_timestamp
                )
                
                if news_item.link:
                    news_items.append(news_item)
                    
            except Exception as e:
                logger.error(f"Error converting Dev.to API article: {str(e)}")
                continue
        
        return news_items
    
    async def _search_with_scraping(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Fallback scraping method."""
        try:
            # Build search query
            search_query = query
            if category:
                search_query = f"{query} {category.value}"
            
            params = {
                'q': search_query,
                'sort_by': 'published_at',
                'sort_direction': 'desc'
            }
            
            # Use different headers for scraping
            scraping_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Referer': 'https://dev.to/',
                'Connection': 'keep-alive'
            }
            
            response = self.session.get(self.search_url, params=params, headers=scraping_headers, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find Dev.to articles with updated selectors
            article_selectors = [
                'div.crayons-story',
                'article.crayons-story',
                'div[data-content-user-id]',
                'div.substory',
                'article'
            ]
            
            articles = []
            for selector in article_selectors:
                articles = soup.select(selector)
                if articles:
                    logger.info(f"Found {len(articles)} articles using selector: {selector}")
                    break
            
            news_items = []
            scraped_timestamp = datetime.utcnow()
            
            for article in articles[:limit]:
                try:
                    # Find title with multiple selectors
                    title_selectors = [
                        'h1 a',
                        'h2 a', 
                        'h3 a',
                        'a.crayons-story__title',
                        '.crayons-story__title a',
                        'a[data-preload]'
                    ]
                    
                    title_elem = None
                    for selector in title_selectors:
                        title_elem = article.select_one(selector)
                        if title_elem:
                            break
                    
                    if not title_elem:
                        continue
                        
                    title = clean_text(title_elem.get_text())
                    if not title or len(title) < 10:
                        continue
                    
                    link = title_elem.get('href', '')
                    if link.startswith('/'):
                        link = f"https://dev.to{link}"
                    elif not link.startswith('http'):
                        continue
                    
                    # Find snippet with better selectors
                    snippet_selectors = [
                        '.crayons-story__snippet',
                        '.crayons-story__summary',
                        '.crayons-story__body',
                        'p',
                        'div[data-content]'
                    ]
                    snippet = "No description available"
                    
                    for selector in snippet_selectors:
                        snippet_elem = article.select_one(selector)
                        if snippet_elem:
                            potential_snippet = clean_text(snippet_elem.get_text())
                            if potential_snippet and len(potential_snippet) > 20:
                                snippet = potential_snippet
                                break
                    
                    news_items.append(NewsItem(
                        title=title,
                        link=link,
                        source_name=self.source_name,
                        snippet=snippet[:500],
                        published_date=None,
                        scraped_timestamp=scraped_timestamp
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing Dev.to article: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} articles from Dev.to scraping")
            return news_items
            
        except Exception as e:
            logger.error(f"Error scraping Dev.to: {str(e)}")
            return []


class BBCNewsScraper(BaseScraper):
    """Scraper for BBC News."""
    
    def __init__(self):
        super().__init__("BBC News")
        self.base_url = "https://www.bbc.com/search"
    
    async def search(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search BBC News for articles."""
        try:
            search_query = query
            if category:
                search_query = f"{query} {category.value}"
            
            params = {
                'q': search_query,
                'filter': 'news'
            }
            
            logger.info(f"Searching BBC News for: {search_query}")
            
            response = self.session.get(self.base_url, params=params, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find BBC articles
            articles = soup.select('div[data-testid="search-result"]') or soup.select('article') or soup.select('div.ssrcss-1f3bvyz-Stack')
            
            news_items = []
            scraped_timestamp = datetime.utcnow()
            
            for article in articles[:limit]:
                try:
                    # Find title and link
                    title_elem = article.select_one('h1 a') or article.select_one('h2 a') or article.select_one('h3 a') or article.select_one('a')
                    if not title_elem:
                        continue
                        
                    title = clean_text(title_elem.get_text())
                    if not title or len(title) < 10:
                        continue
                    
                    link = title_elem.get('href', '')
                    if link.startswith('/'):
                        link = f"https://www.bbc.com{link}"
                    elif not link.startswith('http'):
                        continue
                    
                    # Find snippet
                    snippet_elem = article.select_one('p') or article.select_one('div.ssrcss-1q0x1qg-Paragraph')
                    snippet = clean_text(snippet_elem.get_text()) if snippet_elem else "No description available"
                    
                    news_items.append(NewsItem(
                        title=title,
                        link=link,
                        source_name=self.source_name,
                        snippet=snippet[:500],
                        published_date=None,
                        scraped_timestamp=scraped_timestamp
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing BBC article: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} articles from BBC News")
            return news_items
            
        except Exception as e:
            logger.error(f"Error searching BBC News: {str(e)}")
            return []


class CNNScraper(BaseScraper):
    """Scraper for CNN News."""
    
    def __init__(self):
        super().__init__("CNN")
        self.base_url = "https://edition.cnn.com/search"
    
    async def search(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search CNN for articles."""
        try:
            search_query = query
            if category:
                search_query = f"{query} {category.value}"
            
            params = {
                'q': search_query,
                'size': str(limit),
                'from': '0'
            }
            
            logger.info(f"Searching CNN for: {search_query}")
            
            response = self.session.get(self.base_url, params=params, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find CNN articles
            articles = soup.select('div.cnn-search__result') or soup.select('article') or soup.select('div.container__item')
            
            news_items = []
            scraped_timestamp = datetime.utcnow()
            
            for article in articles[:limit]:
                try:
                    # Find title and link
                    title_elem = article.select_one('h3 a') or article.select_one('h2 a') or article.select_one('a')
                    if not title_elem:
                        continue
                        
                    title = clean_text(title_elem.get_text())
                    if not title or len(title) < 10:
                        continue
                    
                    link = title_elem.get('href', '')
                    if link.startswith('/'):
                        link = f"https://edition.cnn.com{link}"
                    elif not link.startswith('http'):
                        continue
                    
                    # Find snippet
                    snippet_elem = article.select_one('div.cnn-search__result-body') or article.select_one('p')
                    snippet = clean_text(snippet_elem.get_text()) if snippet_elem else "No description available"
                    
                    news_items.append(NewsItem(
                        title=title,
                        link=link,
                        source_name=self.source_name,
                        snippet=snippet[:500],
                        published_date=None,
                        scraped_timestamp=scraped_timestamp
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing CNN article: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} articles from CNN")
            return news_items
            
        except Exception as e:
            logger.error(f"Error searching CNN: {str(e)}")
            return []


class DetikScraper(BaseScraper):
    """Scraper for Detik.com (Indonesian news)."""
    
    def __init__(self):
        super().__init__("Detik")
        self.base_url = "https://www.detik.com/search/searchall"
    
    async def search(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search Detik for articles."""
        try:
            search_query = query
            if category:
                search_query = f"{query} {category.value}"
            
            params = {
                'query': search_query,
                'sortby': 'time'
            }
            
            logger.info(f"Searching Detik for: {search_query}")
            
            response = self.session.get(self.base_url, params=params, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find Detik articles
            articles = soup.select('article') or soup.select('div.list-content__item') or soup.select('div.media__text')
            
            news_items = []
            scraped_timestamp = datetime.utcnow()
            
            for article in articles[:limit]:
                try:
                    # Find title and link
                    title_elem = article.select_one('h2 a') or article.select_one('h3 a') or article.select_one('a.media__link')
                    if not title_elem:
                        continue
                        
                    title = clean_text(title_elem.get_text())
                    if not title or len(title) < 10:
                        continue
                    
                    link = title_elem.get('href', '')
                    if link.startswith('/'):
                        link = f"https://www.detik.com{link}"
                    elif not link.startswith('http'):
                        continue
                    
                    # Find snippet
                    snippet_elem = article.select_one('p') or article.select_one('div.media__desc')
                    snippet = clean_text(snippet_elem.get_text()) if snippet_elem else "No description available"
                    
                    news_items.append(NewsItem(
                        title=title,
                        link=link,
                        source_name=self.source_name,
                        snippet=snippet[:500],
                        published_date=None,
                        scraped_timestamp=scraped_timestamp
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing Detik article: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} articles from Detik")
            return news_items
            
        except Exception as e:
            logger.error(f"Error searching Detik: {str(e)}")
            return []


class KompasScraper(BaseScraper):
    """Scraper for Kompas.com (Indonesian news)."""
    
    def __init__(self):
        super().__init__("Kompas")
        self.base_url = "https://www.kompas.com/search"
    
    async def search(self, query: str, category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
        """Search Kompas for articles."""
        try:
            search_query = query
            if category:
                search_query = f"{query} {category.value}"
            
            params = {
                'q': search_query,
                'site': 'all'
            }
            
            logger.info(f"Searching Kompas for: {search_query}")
            
            response = self.session.get(self.base_url, params=params, timeout=15)
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find Kompas articles
            articles = soup.select('div.article__list') or soup.select('article') or soup.select('div.article__asset')
            
            news_items = []
            scraped_timestamp = datetime.utcnow()
            
            for article in articles[:limit]:
                try:
                    # Find title and link
                    title_elem = article.select_one('h2 a') or article.select_one('h3 a') or article.select_one('a')
                    if not title_elem:
                        continue
                        
                    title = clean_text(title_elem.get_text())
                    if not title or len(title) < 10:
                        continue
                    
                    link = title_elem.get('href', '')
                    if not link.startswith('http'):
                        continue
                    
                    # Find snippet
                    snippet_elem = article.select_one('p') or article.select_one('div.article__subtitle')
                    snippet = clean_text(snippet_elem.get_text()) if snippet_elem else "No description available"
                    
                    news_items.append(NewsItem(
                        title=title,
                        link=link,
                        source_name=self.source_name,
                        snippet=snippet[:500],
                        published_date=None,
                        scraped_timestamp=scraped_timestamp
                    ))
                    
                except Exception as e:
                    logger.error(f"Error parsing Kompas article: {str(e)}")
                    continue
            
            logger.info(f"Found {len(news_items)} articles from Kompas")
            return news_items
            
        except Exception as e:
            logger.error(f"Error searching Kompas: {str(e)}")
            return []


class ArticleScraper:
    """Scraper for individual article content."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def scrape_article(self, url: str) -> Dict[str, Any]:
        """
        Scrape content from a single article URL.
        
        Args:
            url: URL of the article to scrape
            
        Returns:
            Dict containing article data
        """
        try:
            logger.info(f"Scraping article: {url}")
            
            # Use BeautifulSoup directly for now (newspaper3k has build issues)
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('title') or soup.find('h1')
            title = clean_text(title_elem.get_text()) if title_elem else "No title found"
            
            # Extract main content
            content_selectors = [
                'article',
                '.article-content',
                '.post-content',
                '.entry-content',
                '.content',
                'main',
                '.main-content'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove script and style elements
                    for script in content_elem(["script", "style"]):
                        script.decompose()
                    content = clean_text(content_elem.get_text())
                    break
            
            if not content:
                # Last resort: get all paragraph text
                paragraphs = soup.find_all('p')
                content = ' '.join([clean_text(p.get_text()) for p in paragraphs])
            
            # Try to extract author
            author_selectors = [
                '.author',
                '.byline',
                '[rel="author"]',
                '.writer'
            ]
            
            author = None
            for selector in author_selectors:
                author_elem = soup.select_one(selector)
                if author_elem:
                    author = clean_text(author_elem.get_text())
                    break
            
            return {
                'title': title,
                'author': author,
                'content': content,
                'publish_date': None,
                'url': url,
                'status': 'success'
            }
                
        except Exception as e:
            logger.error(f"Error scraping article {url}: {str(e)}")
            return {
                'title': None,
                'author': None,
                'content': None,
                'publish_date': None,
                'url': url,
                'status': 'error',
                'error': str(e)
            }


# Initialize scrapers with priority order (Google Search first)
scrapers = {
    'google_search': GoogleSearchScraper(),  # Priority scraper with original URLs
    'google_news': GoogleNewsScraper(),
    'bing_news': BingNewsScraper(),
    'duckduckgo': DuckDuckGoScraper(),       # Google alternative
    'medium': MediumScraper(),               # Tech/blog articles
    'devto': DevToScraper(),                 # Developer articles
    'bbc_news': BBCNewsScraper(),            # International news
    'cnn': CNNScraper(),                     # International news
    'detik': DetikScraper(),                 # Indonesian news
    'kompas': KompasScraper()                # Indonesian news
}

article_scraper = ArticleScraper()


async def search_news(query: str, sources: Optional[List[str]] = None, 
                     category: Optional[NewsCategory] = None, limit: int = 10) -> List[NewsItem]:
    """
    Search for news across multiple sources with priority order.
    
    Args:
        query: Search query
        sources: List of source names to search (None for all with priority order)
        category: News category filter
        limit: Maximum results per source
        
    Returns:
        List[NewsItem]: Combined results from all sources
    """
    if sources is None:
        # Default priority order: Search engines first, then specific news sites
        sources = [
            'google_search',    # Priority scraper with original URLs
            'duckduckgo',       # Google alternative 
            'google_news',      # Google News RSS
            'bing_news',        # Bing News
            'bbc_news',         # International news
            'cnn',              # International news
            'detik',            # Indonesian news
            'kompas',           # Indonesian news
            'medium',           # Tech/blog articles
            'devto'             # Developer articles
        ]
    
    all_results = []
    
    # Search each source in priority order
    for source_name in sources:
        if source_name in scrapers:
            try:
                logger.info(f"Searching {source_name} for: {query}")
                results = await scrapers[source_name].search(query, category, limit)
                if results:
                    all_results.extend(results)
                    logger.info(f"Got {len(results)} results from {source_name}")
                else:
                    logger.warning(f"No results from {source_name}")
            except Exception as e:
                logger.error(f"Error searching {source_name}: {str(e)}")
        else:
            logger.warning(f"Unknown source: {source_name}")
    
    # Remove duplicates based on title similarity and URL
    unique_results = []
    seen_titles = set()
    seen_urls = set()
    
    for result in all_results:
        title_key = result.title.lower().strip()
        url_key = str(result.link).lower()
        
        if title_key not in seen_titles and url_key not in seen_urls:
            unique_results.append(result)
            seen_titles.add(title_key)
            seen_urls.add(url_key)
    
    # Sort by priority (search engines first) and timestamp
    def sort_key(item):
        source_priority = {
            "Google Search": 0,
            "DuckDuckGo": 1, 
            "Google News": 2,
            "Bing News": 3,
            "BBC News": 4,
            "CNN": 5,
            "Detik": 6,
            "Kompas": 7,
            "Medium": 8,
            "Dev.to": 9
        }
        priority = source_priority.get(item.source_name, 10)
        return (priority, -item.scraped_timestamp.timestamp())
    
    unique_results.sort(key=sort_key)
    
    logger.info(f"Total unique results: {len(unique_results)}")
    return unique_results
