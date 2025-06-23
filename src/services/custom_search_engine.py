"""
Custom Search Engine for Web-Scout MCP Server.

Phase 1 Implementation: Basic search engine with SQLite storage,
web crawler, simple text search, content classification, and ranking.
"""

import asyncio
import hashlib
import json
import logging
import re
import sqlite3
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import aiohttp
import nltk
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .search_models import SearchResult, SearchResponse

logger = logging.getLogger(__name__)

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')


class CustomSearchEngine:
    """Custom search engine with local database and web crawler."""
    
    def __init__(self, db_path: str = "web_scout_search.db", config: Optional[Dict[str, Any]] = None):
        self.db_path = db_path
        self.config = config or {}
        self.session: Optional[aiohttp.ClientSession] = None
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.domain_delays: Dict[str, float] = {}
        self.last_crawl_times: Dict[str, float] = {}
        
        # Configuration
        self.crawl_delay = self.config.get("crawl_delay", 1.0)
        self.max_pages_per_domain = self.config.get("max_pages_per_domain", 1000)
        self.max_content_length = self.config.get("max_content_length", 1000000)  # 1MB
        self.user_agent = self.config.get("user_agent", "Web-Scout-MCP/0.1.0")
        self.request_timeout = self.config.get("request_timeout", 30)
        
        # Initialize database
        self._init_database()
        
        # Load seed URLs
        self.seed_urls = self._get_seed_urls()
    
    def _init_database(self):
        """Initialize SQLite database with the required schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Create pages table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS pages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    domain TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    html TEXT,
                    content_hash TEXT,
                    content_type TEXT DEFAULT 'web',
                    language TEXT,
                    crawl_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_modified TIMESTAMP,
                    page_rank REAL DEFAULT 0.0,
                    quality_score REAL DEFAULT 0.0,
                    status_code INTEGER,
                    content_length INTEGER
                )
            """)
            
            # Create indexes for pages table
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_domain ON pages(domain)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_content_type ON pages(content_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_crawl_timestamp ON pages(crawl_timestamp)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_pages_page_rank ON pages(page_rank DESC)")
            
            # Create FTS5 virtual table for full-text search
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS pages_fts USING fts5(
                    title, content, content=pages, content_rowid=id
                )
            """)
            
            # Create links table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_page_id INTEGER,
                    to_page_id INTEGER,
                    anchor_text TEXT,
                    link_type TEXT DEFAULT 'internal',
                    discovered_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_page_id) REFERENCES pages(id),
                    FOREIGN KEY (to_page_id) REFERENCES pages(id)
                )
            """)
            
            # Create indexes for links table
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_links_from_page ON links(from_page_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_links_to_page ON links(to_page_id)")
            
            # Create images table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    page_id INTEGER,
                    url TEXT NOT NULL,
                    alt_text TEXT,
                    title TEXT,
                    width INTEGER,
                    height INTEGER,
                    file_size INTEGER,
                    content_type TEXT,
                    discovered_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (page_id) REFERENCES pages(id)
                )
            """)
            
            # Create indexes for images table
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_page_id ON images(page_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_images_content_type ON images(content_type)")
            
            # Create crawl queue table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS crawl_queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    domain TEXT,
                    priority INTEGER DEFAULT 5,
                    scheduled_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    retry_count INTEGER DEFAULT 0,
                    last_attempt TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    error_message TEXT
                )
            """)
            
            # Create indexes for crawl queue table
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_crawl_queue_priority_schedule ON crawl_queue(priority DESC, scheduled_time)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_crawl_queue_domain ON crawl_queue(domain)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_crawl_queue_status ON crawl_queue(status)")
            
            conn.commit()
            conn.close()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _get_seed_urls(self) -> List[str]:
        """Get initial seed URLs for crawling."""
        return [
            # High authority sites (Tier 1)
            "https://en.wikipedia.org/wiki/Main_Page",
            "https://www.bbc.com/news",
            "https://www.reuters.com",
            "https://www.theguardian.com",
            "https://stackoverflow.com",
            "https://github.com",
            
            # Educational institutions
            "https://www.mit.edu",
            "https://www.stanford.edu",
            "https://www.harvard.edu",
            
            # Technical documentation
            "https://docs.python.org",
            "https://developer.mozilla.org",
            "https://www.w3.org",
            
            # Reference sites
            "https://www.dictionary.com",
            "https://www.merriam-webster.com",
        ]
    
    async def initialize(self):
        """Initialize the search engine."""
        logger.info("Initializing custom search engine")
        
        # Create HTTP session
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=self.request_timeout)
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={"User-Agent": self.user_agent}
        )
        
        # Check if we need to populate with seed URLs
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM crawl_queue")
        queue_count = cursor.fetchone()[0]
        conn.close()
        
        if queue_count == 0:
            logger.info("Adding seed URLs to crawl queue")
            await self._add_seed_urls()
        
        # Start background crawler
        asyncio.create_task(self._background_crawler())
    
    async def cleanup(self):
        """Clean up resources."""
        if self.session:
            await self.session.close()
    
    async def search(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "web"
    ) -> SearchResponse:
        """
        Search the local index for relevant content.
        
        Args:
            query: Search query
            max_results: Maximum number of results to return
            search_type: Type of search (web, images, news)
        
        Returns:
            SearchResponse with results from local index
        """
        logger.info(f"Searching local index: '{query}' (type: {search_type})")
        
        try:
            if search_type == "images":
                return await self._search_images(query, max_results)
            elif search_type == "news":
                return await self._search_news(query, max_results)
            else:
                return await self._search_web(query, max_results)
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            # Return empty results instead of raising
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_type=search_type
            )
    
    async def _search_web(self, query: str, max_results: int) -> SearchResponse:
        """Search web content using FTS5."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Use FTS5 for full-text search
            search_query = self._prepare_fts_query(query)
            
            cursor.execute("""
                SELECT p.id, p.url, p.title, p.content, p.domain, p.page_rank, 
                       p.quality_score, p.crawl_timestamp, p.content_type
                FROM pages_fts 
                JOIN pages p ON pages_fts.rowid = p.id
                WHERE pages_fts MATCH ?
                ORDER BY bm25(pages_fts) * (1 + p.page_rank) * p.quality_score DESC
                LIMIT ?
            """, (search_query, max_results))
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                page_id, url, title, content, domain, page_rank, quality_score, timestamp, content_type = row
                
                # Create snippet from content
                snippet = self._create_snippet(content or "", query)
                
                result = SearchResult(
                    title=title or "Untitled",
                    url=url,
                    snippet=snippet,
                    source="Custom Search",
                    metadata={
                        "domain": domain,
                        "page_rank": page_rank,
                        "quality_score": quality_score,
                        "content_type": content_type,
                        "timestamp": timestamp
                    }
                )
                results.append(result)
            
            # Get total count
            cursor.execute("SELECT COUNT(*) FROM pages_fts WHERE pages_fts MATCH ?", (search_query,))
            total_results = cursor.fetchone()[0]
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=total_results,
                search_type="web"
            )
        
        finally:
            conn.close()
    
    async def _search_images(self, query: str, max_results: int) -> SearchResponse:
        """Search for images."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Search images by alt text and title
            cursor.execute("""
                SELECT i.url, i.alt_text, i.title, p.url as page_url, p.title as page_title
                FROM images i
                JOIN pages p ON i.page_id = p.id
                WHERE i.alt_text LIKE ? OR i.title LIKE ? OR p.title LIKE ?
                ORDER BY p.page_rank DESC, p.quality_score DESC
                LIMIT ?
            """, (f"%{query}%", f"%{query}%", f"%{query}%", max_results))
            
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                img_url, alt_text, img_title, page_url, page_title = row
                
                result = SearchResult(
                    title=img_title or alt_text or "Image",
                    url=img_url,
                    snippet=alt_text or "",
                    source="Custom Search Images",
                    thumbnail=img_url,
                    metadata={
                        "page_url": page_url,
                        "page_title": page_title
                    }
                )
                results.append(result)
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_type="images"
            )
        
        finally:
            conn.close()
    
    async def _search_news(self, query: str, max_results: int) -> SearchResponse:
        """Search for news content."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Search news content with time preference
            search_query = self._prepare_fts_query(query)
            
            cursor.execute("""
                SELECT p.id, p.url, p.title, p.content, p.domain, p.page_rank, 
                       p.quality_score, p.crawl_timestamp, p.content_type
                FROM pages_fts 
                JOIN pages p ON pages_fts.rowid = p.id
                WHERE pages_fts MATCH ? AND p.content_type = 'news'
                ORDER BY p.crawl_timestamp DESC, bm25(pages_fts) * (1 + p.page_rank) DESC
                LIMIT ?
            """, (search_query, max_results))
            
            rows = cursor.fetchall()
            
            # If no news-specific results, fall back to general search with news domains
            if not rows:
                cursor.execute("""
                    SELECT p.id, p.url, p.title, p.content, p.domain, p.page_rank, 
                           p.quality_score, p.crawl_timestamp, p.content_type
                    FROM pages_fts 
                    JOIN pages p ON pages_fts.rowid = p.id
                    WHERE pages_fts MATCH ? AND (
                        p.domain LIKE '%news%' OR p.domain LIKE '%bbc%' OR 
                        p.domain LIKE '%reuters%' OR p.domain LIKE '%guardian%'
                    )
                    ORDER BY p.crawl_timestamp DESC, bm25(pages_fts) * (1 + p.page_rank) DESC
                    LIMIT ?
                """, (search_query, max_results))
                
                rows = cursor.fetchall()
            
            results = []
            for row in rows:
                page_id, url, title, content, domain, page_rank, quality_score, timestamp, content_type = row
                
                snippet = self._create_snippet(content or "", query)
                
                result = SearchResult(
                    title=title or "Untitled",
                    url=url,
                    snippet=snippet,
                    source="Custom Search News",
                    metadata={
                        "domain": domain,
                        "page_rank": page_rank,
                        "quality_score": quality_score,
                        "content_type": content_type,
                        "timestamp": timestamp
                    }
                )
                results.append(result)
            
            return SearchResponse(
                query=query,
                results=results,
                total_results=len(results),
                search_type="news"
            )
        
        finally:
            conn.close()
    
    def _prepare_fts_query(self, query: str) -> str:
        """Prepare query for FTS5 search."""
        # Remove special characters and normalize
        query = re.sub(r'[^\w\s]', ' ', query)
        terms = query.split()
        
        # Create FTS5 query with OR logic for better recall
        if terms:
            return ' OR '.join(f'"{term}"' for term in terms if len(term) > 2)
        return query
    
    def _create_snippet(self, content: str, query: str, max_length: int = 300) -> str:
        """Create a search result snippet highlighting query terms."""
        if not content:
            return ""
        
        # Find the best excerpt containing query terms
        query_terms = query.lower().split()
        content_lower = content.lower()
        
        # Find positions of query terms
        positions = []
        for term in query_terms:
            if len(term) > 2:
                start = 0
                while True:
                    pos = content_lower.find(term, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1
        
        if positions:
            # Find the best position to center the snippet
            center_pos = min(positions)
            start_pos = max(0, center_pos - max_length // 2)
            end_pos = min(len(content), start_pos + max_length)
            
            snippet = content[start_pos:end_pos]
            
            # Add ellipsis if truncated
            if start_pos > 0:
                snippet = "..." + snippet
            if end_pos < len(content):
                snippet = snippet + "..."
        else:
            # No query terms found, take beginning
            snippet = content[:max_length]
            if len(content) > max_length:
                snippet += "..."
        
        return snippet.strip()
    
    async def _add_seed_urls(self):
        """Add seed URLs to the crawl queue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            for url in self.seed_urls:
                domain = urlparse(url).netloc
                cursor.execute("""
                    INSERT OR IGNORE INTO crawl_queue (url, domain, priority)
                    VALUES (?, ?, ?)
                """, (url, domain, 1))  # High priority for seed URLs
            
            conn.commit()
            logger.info(f"Added {len(self.seed_urls)} seed URLs to crawl queue")
        
        finally:
            conn.close()
    
    async def _background_crawler(self):
        """Background task that continuously crawls URLs from the queue."""
        logger.info("Starting background crawler")
        
        while True:
            try:
                # Get next URL to crawl
                url = await self._get_next_crawl_url()
                
                if url:
                    await self._crawl_url(url)
                    
                    # Small delay between crawls
                    await asyncio.sleep(0.1)
                else:
                    # No URLs to crawl, wait longer
                    await asyncio.sleep(10)
            
            except Exception as e:
                logger.error(f"Background crawler error: {e}")
                await asyncio.sleep(5)
    
    async def _get_next_crawl_url(self) -> Optional[str]:
        """Get the next URL to crawl from the queue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get next pending URL with highest priority
            cursor.execute("""
                SELECT url FROM crawl_queue
                WHERE status = 'pending' AND (
                    last_attempt IS NULL OR 
                    datetime(last_attempt) < datetime('now', '-1 hour')
                )
                ORDER BY priority DESC, scheduled_time ASC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                url = row[0]
                
                # Mark as crawling
                cursor.execute("""
                    UPDATE crawl_queue 
                    SET status = 'crawling', last_attempt = CURRENT_TIMESTAMP
                    WHERE url = ?
                """, (url,))
                
                conn.commit()
                return url
            
            return None
        
        finally:
            conn.close()
    
    async def _crawl_url(self, url: str):
        """Crawl a single URL."""
        domain = urlparse(url).netloc
        
        try:
            # Check robots.txt
            if not await self._can_crawl_url(url):
                await self._mark_crawl_completed(url, "robots_blocked")
                return
            
            # Respect crawl delay
            await self._respect_crawl_delay(domain)
            
            # Fetch the page
            async with self.session.get(url) as response:
                if response.status != 200:
                    await self._mark_crawl_failed(url, f"HTTP {response.status}")
                    return
                
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    await self._mark_crawl_completed(url, "not_html")
                    return
                
                html = await response.text()
                
                if len(html) > self.max_content_length:
                    await self._mark_crawl_failed(url, "content_too_large")
                    return
            
            # Process the page
            await self._process_page(url, html, response.status)
            await self._mark_crawl_completed(url, "completed")
            
            logger.debug(f"Successfully crawled: {url}")
        
        except Exception as e:
            logger.error(f"Failed to crawl {url}: {e}")
            await self._mark_crawl_failed(url, str(e))
    
    async def _can_crawl_url(self, url: str) -> bool:
        """Check if URL can be crawled according to robots.txt."""
        domain = urlparse(url).netloc
        
        if domain not in self.robots_cache:
            try:
                robots_url = f"https://{domain}/robots.txt"
                rp = RobotFileParser()
                rp.set_url(robots_url)
                
                # Fetch robots.txt
                async with self.session.get(robots_url) as response:
                    if response.status == 200:
                        robots_content = await response.text()
                        # Parse robots.txt content manually since urllib.robotparser is synchronous
                        self.robots_cache[domain] = self._parse_robots_txt(robots_content)
                    else:
                        # No robots.txt or error, assume allowed
                        self.robots_cache[domain] = {"allowed": True, "delay": None}
            
            except Exception:
                # Error fetching robots.txt, assume allowed
                self.robots_cache[domain] = {"allowed": True, "delay": None}
        
        robots = self.robots_cache[domain]
        return robots.get("allowed", True)
    
    def _parse_robots_txt(self, content: str) -> Dict[str, Any]:
        """Basic robots.txt parser."""
        lines = content.split('\n')
        current_user_agent = None
        rules = {"allowed": True, "delay": None}
        
        for line in lines:
            line = line.strip()
            if line.startswith('#') or not line:
                continue
            
            if line.lower().startswith('user-agent:'):
                user_agent = line.split(':', 1)[1].strip()
                if user_agent == '*' or 'web-scout' in user_agent.lower():
                    current_user_agent = user_agent
            
            elif current_user_agent and line.lower().startswith('disallow:'):
                path = line.split(':', 1)[1].strip()
                if path == '/':
                    rules["allowed"] = False
            
            elif current_user_agent and line.lower().startswith('crawl-delay:'):
                try:
                    delay = float(line.split(':', 1)[1].strip())
                    rules["delay"] = delay
                except ValueError:
                    pass
        
        return rules
    
    async def _respect_crawl_delay(self, domain: str):
        """Respect crawl delay for domain."""
        # Get delay from robots.txt or use default
        robots = self.robots_cache.get(domain, {})
        delay = robots.get("delay")
        
        # Use default if delay is None
        if delay is None:
            delay = self.crawl_delay
        
        # Check last crawl time
        last_crawl = self.last_crawl_times.get(domain, 0)
        now = time.time()
        
        if now - last_crawl < delay:
            sleep_time = delay - (now - last_crawl)
            await asyncio.sleep(sleep_time)
        
        self.last_crawl_times[domain] = time.time()
    
    async def _process_page(self, url: str, html: str, status_code: int):
        """Process crawled page and extract content."""
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Extract basic information
            title = self._extract_title(soup)
            content = self._extract_content(soup)
            content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
            domain = urlparse(url).netloc
            
            # Classify content
            content_type = self._classify_content(url, title, content, soup)
            
            # Calculate quality score
            quality_score = self._calculate_quality_score(soup, content)
            
            # Store page in database
            page_id = await self._store_page(
                url=url,
                domain=domain,
                title=title,
                content=content,
                html=html,
                content_hash=content_hash,
                content_type=content_type,
                quality_score=quality_score,
                status_code=status_code,
                content_length=len(content)
            )
            
            # Extract and store images
            await self._extract_images(soup, page_id, url)
            
            # Extract links for future crawling
            await self._extract_links(soup, page_id, url, domain)
        
        except Exception as e:
            logger.error(f"Failed to process page {url}: {e}")
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        # Fallback to h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return ""
    
    def _extract_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from page."""
        # Remove script, style, and other non-content tags
        for tag in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            tag.decompose()
        
        # Try to find main content area
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_=re.compile(r'content|main|body'))
        
        if main_content:
            text = main_content.get_text()
        else:
            text = soup.get_text()
        
        # Clean up text
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(line for line in lines if line)
        
        return text[:10000]  # Limit to reasonable size
    
    def _classify_content(self, url: str, title: str, content: str, soup: BeautifulSoup) -> str:
        """Classify content type."""
        url_lower = url.lower()
        title_lower = title.lower()
        content_lower = content.lower()
        
        # News classification
        news_indicators = [
            any(domain in url_lower for domain in ['news', 'bbc', 'reuters', 'guardian', 'cnn']),
            any(keyword in title_lower for keyword in ['news', 'breaking', 'report']),
            soup.find('time') is not None,
            any(keyword in content_lower for keyword in ['published', 'reporter', 'breaking news'])
        ]
        
        if sum(news_indicators) >= 2:
            return 'news'
        
        # Academic classification
        academic_indicators = [
            '.edu' in url_lower,
            any(keyword in title_lower for keyword in ['research', 'study', 'journal', 'paper']),
            any(keyword in content_lower for keyword in ['abstract', 'methodology', 'conclusion', 'references'])
        ]
        
        if sum(academic_indicators) >= 2:
            return 'academic'
        
        # Reference classification
        reference_indicators = [
            any(domain in url_lower for domain in ['wikipedia', 'dictionary', 'encyclopedia']),
            any(keyword in title_lower for keyword in ['definition', 'meaning', 'what is'])
        ]
        
        if sum(reference_indicators) >= 1:
            return 'reference'
        
        return 'web'
    
    def _calculate_quality_score(self, soup: BeautifulSoup, content: str) -> float:
        """Calculate content quality score (0.0 to 1.0)."""
        score = 0.0
        
        # Content length (optimal around 1000-3000 chars)
        content_len = len(content)
        if 500 <= content_len <= 5000:
            score += 0.2
        elif content_len > 300:
            score += 0.1
        
        # Presence of headings
        headings = soup.find_all(['h1', 'h2', 'h3'])
        if len(headings) >= 2:
            score += 0.2
        elif len(headings) >= 1:
            score += 0.1
        
        # Presence of images
        images = soup.find_all('img')
        if len(images) >= 1:
            score += 0.1
        
        # Proper HTML structure
        if soup.find('main') or soup.find('article'):
            score += 0.1
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            score += 0.1
        
        # External links (indicates reference quality)
        external_links = len([a for a in soup.find_all('a', href=True) 
                            if a['href'].startswith('http')])
        if external_links >= 3:
            score += 0.1
        
        # Title exists and is reasonable length
        title = soup.find('title')
        if title and 10 <= len(title.get_text()) <= 100:
            score += 0.1
        
        # Language indicators (English preferred for now)
        if soup.find('html', lang=re.compile(r'en', re.I)):
            score += 0.1
        
        return min(score, 1.0)
    
    async def _store_page(self, **kwargs) -> int:
        """Store page in database and return page ID."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                INSERT OR REPLACE INTO pages (
                    url, domain, title, content, html, content_hash, content_type,
                    quality_score, status_code, content_length, crawl_timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                kwargs['url'], kwargs['domain'], kwargs['title'], kwargs['content'],
                kwargs['html'], kwargs['content_hash'], kwargs['content_type'],
                kwargs['quality_score'], kwargs['status_code'], kwargs['content_length']
            ))
            
            page_id = cursor.lastrowid
            
            # Update FTS index
            cursor.execute("""
                INSERT OR REPLACE INTO pages_fts (rowid, title, content)
                VALUES (?, ?, ?)
            """, (page_id, kwargs['title'], kwargs['content']))
            
            conn.commit()
            return page_id
        
        finally:
            conn.close()
    
    async def _extract_images(self, soup: BeautifulSoup, page_id: int, page_url: str):
        """Extract and store image information."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            images = soup.find_all('img')
            for img in images[:10]:  # Limit to 10 images per page
                src = img.get('src')
                if not src:
                    continue
                
                # Make URL absolute
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = urljoin(page_url, src)
                elif not src.startswith('http'):
                    src = urljoin(page_url, src)
                
                alt_text = img.get('alt', '').strip()
                title = img.get('title', '').strip()
                width = img.get('width')
                height = img.get('height')
                
                try:
                    width = int(width) if width else None
                    height = int(height) if height else None
                except ValueError:
                    width = height = None
                
                cursor.execute("""
                    INSERT OR IGNORE INTO images (
                        page_id, url, alt_text, title, width, height
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (page_id, src, alt_text, title, width, height))
            
            conn.commit()
        
        finally:
            conn.close()
    
    async def _extract_links(self, soup: BeautifulSoup, page_id: int, page_url: str, domain: str):
        """Extract links for future crawling."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            links = soup.find_all('a', href=True)
            
            for link in links[:50]:  # Limit links per page
                href = link['href']
                anchor_text = link.get_text().strip()
                
                # Make URL absolute
                if href.startswith('//'):
                    href = 'https:' + href
                elif href.startswith('/'):
                    href = urljoin(page_url, href)
                elif not href.startswith('http'):
                    href = urljoin(page_url, href)
                
                # Skip invalid URLs
                if not href.startswith('http'):
                    continue
                
                link_domain = urlparse(href).netloc
                
                # Determine link type
                link_type = 'internal' if link_domain == domain else 'external'
                
                # Add to crawl queue if it's a new internal or high-value external link
                if link_type == 'internal' or self._is_valuable_external_link(link_domain):
                    # Check current page count for domain
                    cursor.execute("SELECT COUNT(*) FROM pages WHERE domain = ?", (link_domain,))
                    domain_pages = cursor.fetchone()[0]
                    
                    if domain_pages < self.max_pages_per_domain:
                        priority = 5 if link_type == 'internal' else 3
                        cursor.execute("""
                            INSERT OR IGNORE INTO crawl_queue (url, domain, priority)
                            VALUES (?, ?, ?)
                        """, (href, link_domain, priority))
            
            conn.commit()
        
        finally:
            conn.close()
    
    def _is_valuable_external_link(self, domain: str) -> bool:
        """Check if external domain is valuable for crawling."""
        valuable_domains = [
            'wikipedia.org', 'github.com', 'stackoverflow.com', 'medium.com',
            'bbc.com', 'reuters.com', 'theguardian.com', 'news.ycombinator.com',
            'arxiv.org', 'scholar.google.com', 'jstor.org'
        ]
        
        return any(valuable in domain for valuable in valuable_domains)
    
    async def _mark_crawl_completed(self, url: str, status: str):
        """Mark URL as completed in crawl queue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE crawl_queue 
                SET status = 'completed', error_message = ?
                WHERE url = ?
            """, (status, url))
            conn.commit()
        
        finally:
            conn.close()
    
    async def _mark_crawl_failed(self, url: str, error: str):
        """Mark URL as failed in crawl queue."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                UPDATE crawl_queue 
                SET status = 'failed', error_message = ?, retry_count = retry_count + 1
                WHERE url = ?
            """, (error, url))
            
            # Reset to pending if retry count is low
            cursor.execute("""
                UPDATE crawl_queue 
                SET status = 'pending', scheduled_time = datetime('now', '+1 hour')
                WHERE url = ? AND retry_count < 3
            """, (url,))
            
            conn.commit()
        
        finally:
            conn.close()
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get search engine statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Page statistics
            cursor.execute("SELECT COUNT(*) FROM pages")
            stats['total_pages'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT domain) FROM pages")
            stats['total_domains'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT content_type, COUNT(*) FROM pages GROUP BY content_type")
            stats['pages_by_type'] = dict(cursor.fetchall())
            
            # Queue statistics
            cursor.execute("SELECT status, COUNT(*) FROM crawl_queue GROUP BY status")
            stats['queue_by_status'] = dict(cursor.fetchall())
            
            # Image statistics
            cursor.execute("SELECT COUNT(*) FROM images")
            stats['total_images'] = cursor.fetchone()[0]
            
            return stats
        
        finally:
            conn.close()