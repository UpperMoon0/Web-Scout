"""
Web scraping service for the Web Scout MCP Server.

Provides functionality for scraping web content using both simple HTTP requests
and JavaScript-enabled browser automation.
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)


class ScrapingResult:
    """Represents the result of a web scraping operation."""
    
    def __init__(
        self,
        url: str,
        title: str,
        content: str,
        html: str,
        links: List[str],
        images: List[str],
        metadata: Dict[str, Any],
        timestamp: Optional[str] = None,
    ):
        self.url = url
        self.title = title
        self.content = content
        self.html = html
        self.links = links
        self.images = images
        self.metadata = metadata
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content,
            "html": self.html,
            "links": self.links,
            "images": self.images,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
        }


class ScrapingHistory:
    """Represents a scraping operation history entry."""
    
    def __init__(self, url: str, success: bool, error: Optional[str] = None):
        self.url = url
        self.timestamp = datetime.now().isoformat()
        self.success = success
        self.error = error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "url": self.url,
            "timestamp": self.timestamp,
            "success": self.success,
            "error": self.error,
        }


class ScrapingService:
    """Service for web scraping operations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.user_agent = config.get("user_agent", "Web-Scout-MCP/0.1.0")
        self.max_retries = config.get("max_retries", 3)
        self.timeout = config.get("timeout", 30)
        self.enable_headless = config.get("enable_headless", True)
        self.cache_dir = config.get("cache_dir", ".web_scout_cache")
        
        self.history: List[ScrapingHistory] = []
        self.content_cache: Dict[str, str] = {}
        self.driver: Optional[webdriver.Chrome] = None
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def initialize(self):
        """Initialize the scraping service."""
        logger.info("Initializing scraping service")
        # Load cached history if exists
        await self._load_history()
    
    async def scrape_url(
        self,
        url: str,
        use_javascript: bool = False,
        extract_links: bool = True,
        extract_images: bool = True,
    ) -> ScrapingResult:
        """
        Scrape content from a URL.
        
        Args:
            url: The URL to scrape
            use_javascript: Whether to use JavaScript rendering
            extract_links: Whether to extract links
            extract_images: Whether to extract images
        
        Returns:
            ScrapingResult object containing the scraped data
        """
        logger.info(f"Scraping URL: {url} (JS: {use_javascript})")
        
        try:
            if use_javascript:
                result = await self._scrape_with_selenium(url, extract_links, extract_images)
            else:
                result = await self._scrape_with_requests(url, extract_links, extract_images)
            
            # Cache the content
            domain = urlparse(url).netloc
            self.content_cache[domain] = result.content
            
            # Add to history
            self.history.append(ScrapingHistory(url, True))
            await self._save_history()
            
            return result
        
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to scrape {url}: {error_msg}")
            
            # Add to history
            self.history.append(ScrapingHistory(url, False, error_msg))
            await self._save_history()
            
            raise
    
    async def _scrape_with_requests(
        self, url: str, extract_links: bool, extract_images: bool
    ) -> ScrapingResult:
        """Scrape using simple HTTP requests."""
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(f"HTTP {response.status}: {response.reason}")
                
                html = await response.text()
        
        return self._extract_content(url, html, extract_links, extract_images)
    
    async def _scrape_with_selenium(
        self, url: str, extract_links: bool, extract_images: bool
    ) -> ScrapingResult:
        """Scrape using Selenium for JavaScript support."""
        if not self.driver:
            self._setup_selenium_driver()
        
        try:
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, self.timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Get page source after JavaScript execution
            html = self.driver.page_source
            
            return self._extract_content(url, html, extract_links, extract_images)
        
        except Exception as e:
            logger.error(f"Selenium scraping failed: {e}")
            raise
    
    def _setup_selenium_driver(self):
        """Set up Selenium Chrome driver."""
        chrome_options = Options()
        
        if self.enable_headless:
            chrome_options.add_argument("--headless")
        
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument(f"--user-agent={self.user_agent}")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(self.timeout)
    
    def _extract_content(
        self, url: str, html: str, extract_links: bool, extract_images: bool
    ) -> ScrapingResult:
        """Extract content from HTML."""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract title
        title_tag = soup.find('title')
        title = title_tag.get_text().strip() if title_tag else ""
        if not title:
            h1_tag = soup.find('h1')
            title = h1_tag.get_text().strip() if h1_tag else "No title"
        
        # Remove script and style elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside"]):
            element.decompose()
        
        # Extract text content
        content = soup.get_text()
        # Clean up whitespace
        content = ' '.join(content.split())
        
        # Extract links
        links = []
        if extract_links:
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                links.append(absolute_url)
        
        # Extract images
        images = []
        if extract_images:
            for img in soup.find_all('img', src=True):
                src = img['src']
                absolute_url = urljoin(url, src)
                images.append(absolute_url)
        
        # Extract metadata
        metadata = self._extract_metadata(soup)
        
        return ScrapingResult(
            url=url,
            title=title,
            content=content,
            html=html,
            links=list(set(links)),  # Remove duplicates
            images=list(set(images)),  # Remove duplicates
            metadata=metadata,
        )
    
    def _extract_metadata(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract metadata from HTML."""
        metadata = {}
        
        # Basic meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            property_name = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            if name in ['description', 'keywords', 'author']:
                metadata[name] = content
            elif property_name.startswith('og:'):
                if 'open_graph' not in metadata:
                    metadata['open_graph'] = {}
                metadata['open_graph'][property_name[3:]] = content
            elif property_name.startswith('twitter:'):
                if 'twitter' not in metadata:
                    metadata['twitter'] = {}
                metadata['twitter'][property_name[8:]] = content
        
        # Canonical URL
        canonical = soup.find('link', rel='canonical')
        if canonical and canonical.get('href'):
            metadata['canonical'] = canonical['href']
        
        # Language
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            metadata['language'] = html_tag['lang']
        
        return metadata
    
    async def get_scraping_history(self) -> List[Dict[str, Any]]:
        """Get the scraping history."""
        return [entry.to_dict() for entry in self.history[-100:]]  # Last 100 entries
    
    async def get_cached_content(self, domain: str) -> Optional[str]:
        """Get cached content for a domain."""
        return self.content_cache.get(domain)
    
    async def _load_history(self):
        """Load scraping history from cache."""
        history_file = os.path.join(self.cache_dir, "scraping_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    history_data = json.load(f)
                
                self.history = [
                    ScrapingHistory(
                        url=entry['url'],
                        success=entry['success'],
                        error=entry.get('error')
                    ) for entry in history_data
                ]
            except Exception as e:
                logger.warning(f"Failed to load history: {e}")
    
    async def _save_history(self):
        """Save scraping history to cache."""
        history_file = os.path.join(self.cache_dir, "scraping_history.json")
        try:
            history_data = [entry.to_dict() for entry in self.history[-100:]]
            with open(history_file, 'w') as f:
                json.dump(history_data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save history: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        logger.info("Scraping service cleaned up")