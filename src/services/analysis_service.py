"""
Analysis service for the Web Scout MCP Server.

Provides functionality for website analysis, content analysis,
SEO analysis, performance analysis, and more.
"""

import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import pandas as pd
import numpy as np
from bs4 import BeautifulSoup
from textblob import TextBlob

logger = logging.getLogger(__name__)


class WebsiteAnalysis:
    """Represents a comprehensive website analysis."""
    
    def __init__(
        self,
        domain: str,
        url: str,
        title: str,
        description: str,
        technologies: List[str],
        performance: Dict[str, Any],
        seo: Dict[str, Any],
        accessibility: Dict[str, Any],
        security: Dict[str, Any],
        content: Dict[str, Any],
        timestamp: Optional[str] = None,
    ):
        self.domain = domain
        self.url = url
        self.title = title
        self.description = description
        self.technologies = technologies
        self.performance = performance
        self.seo = seo
        self.accessibility = accessibility
        self.security = security
        self.content = content
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "domain": self.domain,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "technologies": self.technologies,
            "performance": self.performance,
            "seo": self.seo,
            "accessibility": self.accessibility,
            "security": self.security,
            "content": self.content,
            "timestamp": self.timestamp,
        }


class ContentAnalysis:
    """Represents content analysis results."""
    
    def __init__(
        self,
        summary: str,
        key_topics: List[str],
        sentiment: str,
        readability_score: float,
        entities: Dict[str, List[str]],
        language: str = "en",
        word_count: int = 0,
        timestamp: Optional[str] = None,
    ):
        self.summary = summary
        self.key_topics = key_topics
        self.sentiment = sentiment
        self.readability_score = readability_score
        self.entities = entities
        self.language = language
        self.word_count = word_count
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "summary": self.summary,
            "key_topics": self.key_topics,
            "sentiment": self.sentiment,
            "readability_score": self.readability_score,
            "entities": self.entities,
            "language": self.language,
            "word_count": self.word_count,
            "timestamp": self.timestamp,
        }


class AnalysisService:
    """Service for website and content analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.cache_dir = config.get("cache_dir", ".web_scout_cache")
        
        self.analysis_cache: Dict[str, WebsiteAnalysis] = {}
        self.content_analysis_cache: Dict[str, ContentAnalysis] = {}
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
    
    async def initialize(self):
        """Initialize the analysis service."""
        logger.info("Initializing analysis service")
        await self._load_cache()
    
    async def analyze_website(
        self,
        url: str,
        html: str,
        content: str,
        metadata: Dict[str, Any],
        include_seo: bool = True,
        include_performance: bool = True,
        include_accessibility: bool = True,
        include_security: bool = True,
    ) -> WebsiteAnalysis:
        """
        Perform comprehensive website analysis.
        
        Args:
            url: The website URL
            html: The HTML content
            content: The text content
            metadata: Website metadata
            include_seo: Whether to include SEO analysis
            include_performance: Whether to include performance analysis
            include_accessibility: Whether to include accessibility analysis
            include_security: Whether to include security analysis
        
        Returns:
            WebsiteAnalysis object containing the analysis results
        """
        logger.info(f"Analyzing website: {url}")
        
        domain = urlparse(url).netloc
        soup = BeautifulSoup(html, 'html.parser')
        
        # Basic information
        title = metadata.get("title", "") or self._extract_title(soup)
        description = metadata.get("description", "") or self._extract_description(soup)
        
        # Technology detection
        technologies = self._detect_technologies(html, soup)
        
        # Performance analysis
        performance = {}
        if include_performance:
            performance = self._analyze_performance(html, soup)
        
        # SEO analysis
        seo = {}
        if include_seo:
            seo = self._analyze_seo(soup, metadata)
        
        # Accessibility analysis
        accessibility = {}
        if include_accessibility:
            accessibility = self._analyze_accessibility(soup)
        
        # Security analysis
        security = {}
        if include_security:
            security = self._analyze_security(url, html, soup)
        
        # Content analysis
        content_analysis = self._analyze_content_basic(content, html, soup)
        
        analysis = WebsiteAnalysis(
            domain=domain,
            url=url,
            title=title,
            description=description,
            technologies=technologies,
            performance=performance,
            seo=seo,
            accessibility=accessibility,
            security=security,
            content=content_analysis,
        )
        
        # Cache the analysis
        self.analysis_cache[domain] = analysis
        await self._save_cache()
        
        return analysis
    
    async def analyze_content(
        self,
        content: str,
        include_sentiment: bool = True,
        include_entities: bool = True,
        include_keywords: bool = True,
    ) -> ContentAnalysis:
        """
        Analyze text content for insights.
        
        Args:
            content: The text content to analyze
            include_sentiment: Whether to include sentiment analysis
            include_entities: Whether to include entity extraction
            include_keywords: Whether to include keyword extraction
        
        Returns:
            ContentAnalysis object containing the analysis results
        """
        logger.info("Analyzing content")
        
        # Generate cache key
        content_hash = str(hash(content))
        
        # Check cache
        if content_hash in self.content_analysis_cache:
            return self.content_analysis_cache[content_hash]
        
        # Basic text processing
        blob = TextBlob(content)
        words = blob.words
        sentences = blob.sentences
        
        # Word count
        word_count = len(words)
        
        # Language detection
        try:
            language = blob.detect_language()
        except:
            language = "en"
        
        # Summary generation
        summary = self._generate_summary(content, sentences)
        
        # Key topics extraction
        key_topics = []
        if include_keywords:
            key_topics = self._extract_key_topics(words)
        
        # Sentiment analysis
        sentiment = "neutral"
        if include_sentiment and content.strip():
            sentiment = self._analyze_sentiment(blob)
        
        # Readability score
        readability_score = self._calculate_readability(words, sentences)
        
        # Entity extraction
        entities = {}
        if include_entities:
            entities = self._extract_entities(content)
        
        analysis = ContentAnalysis(
            summary=summary,
            key_topics=key_topics,
            sentiment=sentiment,
            readability_score=readability_score,
            entities=entities,
            language=language,
            word_count=word_count,
        )
        
        # Cache the analysis
        self.content_analysis_cache[content_hash] = analysis
        
        return analysis
    
    async def get_cached_analysis(self, domain: str) -> Optional[WebsiteAnalysis]:
        """Get cached website analysis for a domain."""
        return self.analysis_cache.get(domain)
    
    async def get_analysis_cache(self) -> Dict[str, Dict[str, Any]]:
        """Get all cached analyses."""
        return {domain: analysis.to_dict() for domain, analysis in self.analysis_cache.items()}
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract title from HTML."""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
        
        return "No title"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract description from HTML."""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        
        # Fallback to first paragraph
        first_p = soup.find('p')
        if first_p:
            text = first_p.get_text().strip()
            return text[:200] + "..." if len(text) > 200 else text
        
        return ""
    
    def _detect_technologies(self, html: str, soup: BeautifulSoup) -> List[str]:
        """Detect technologies used on the website."""
        technologies = []
        html_lower = html.lower()
        
        # JavaScript frameworks
        if 'react' in html_lower or 'reactdom' in html_lower:
            technologies.append('React')
        if 'vue' in html_lower and ('vue.js' in html_lower or 'vuejs' in html_lower):
            technologies.append('Vue.js')
        if 'angular' in html_lower:
            technologies.append('Angular')
        if 'jquery' in html_lower:
            technologies.append('jQuery')
        
        # CSS frameworks
        if 'bootstrap' in html_lower:
            technologies.append('Bootstrap')
        if 'tailwind' in html_lower:
            technologies.append('Tailwind CSS')
        if 'bulma' in html_lower:
            technologies.append('Bulma')
        
        # CMS detection
        if 'wp-content' in html_lower or 'wordpress' in html_lower:
            technologies.append('WordPress')
        if 'drupal' in html_lower:
            technologies.append('Drupal')
        if 'joomla' in html_lower:
            technologies.append('Joomla')
        
        # E-commerce
        if 'shopify' in html_lower:
            technologies.append('Shopify')
        if 'woocommerce' in html_lower:
            technologies.append('WooCommerce')
        if 'magento' in html_lower:
            technologies.append('Magento')
        
        # Analytics
        if 'google-analytics' in html_lower or 'gtag' in html_lower:
            technologies.append('Google Analytics')
        if 'gtm' in html_lower or 'googletagmanager' in html_lower:
            technologies.append('Google Tag Manager')
        
        # CDNs
        if 'cloudflare' in html_lower:
            technologies.append('Cloudflare')
        if 'amazonaws' in html_lower:
            technologies.append('AWS')
        
        return list(set(technologies))
    
    def _analyze_performance(self, html: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze website performance metrics."""
        # Count various elements
        image_count = len(soup.find_all('img'))
        script_count = len(soup.find_all('script'))
        css_count = len(soup.find_all('link', rel='stylesheet'))
        
        # Page size estimation
        page_size = len(html.encode('utf-8'))
        
        # External resources
        external_scripts = len([s for s in soup.find_all('script') if s.get('src')])
        external_stylesheets = len([l for l in soup.find_all('link', rel='stylesheet') if l.get('href')])
        
        return {
            "page_size_bytes": page_size,
            "image_count": image_count,
            "script_count": script_count,
            "css_count": css_count,
            "external_scripts": external_scripts,
            "external_stylesheets": external_stylesheets,
            "estimated_requests": image_count + external_scripts + external_stylesheets,
        }
    
    def _analyze_seo(self, soup: BeautifulSoup, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze SEO factors."""
        # Title analysis
        title_tag = soup.find('title')
        title_length = len(title_tag.get_text()) if title_tag else 0
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        desc_length = len(meta_desc['content']) if meta_desc and meta_desc.get('content') else 0
        
        # Heading structure
        headings = {}
        for i in range(1, 7):
            headings[f'h{i}'] = len(soup.find_all(f'h{i}'))
        
        # Other SEO elements
        has_canonical = bool(soup.find('link', rel='canonical'))
        has_meta_robots = bool(soup.find('meta', attrs={'name': 'robots'}))
        has_og_tags = bool(soup.find('meta', attrs={'property': lambda x: x and x.startswith('og:')}))
        has_twitter_cards = bool(soup.find('meta', attrs={'name': lambda x: x and x.startswith('twitter:')}))
        
        # Schema markup
        has_json_ld = bool(soup.find('script', type='application/ld+json'))
        has_microdata = bool(soup.find(attrs={'itemscope': True}))
        
        return {
            "title_length": title_length,
            "title_optimal": 30 <= title_length <= 60,
            "meta_description_length": desc_length,
            "meta_description_optimal": 120 <= desc_length <= 160,
            "heading_structure": headings,
            "has_h1": headings.get('h1', 0) > 0,
            "has_canonical": has_canonical,
            "has_meta_robots": has_meta_robots,
            "has_open_graph": has_og_tags,
            "has_twitter_cards": has_twitter_cards,
            "has_structured_data": has_json_ld or has_microdata,
        }
    
    def _analyze_accessibility(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze accessibility factors."""
        # Image alt text
        images = soup.find_all('img')
        images_with_alt = [img for img in images if img.get('alt')]
        alt_text_percentage = (len(images_with_alt) / len(images) * 100) if images else 100
        
        # Form labels
        inputs = soup.find_all('input', type=lambda x: x != 'hidden')
        labeled_inputs = [inp for inp in inputs if inp.get('aria-label') or inp.get('aria-labelledby') or soup.find('label', attrs={'for': inp.get('id')})]
        form_label_percentage = (len(labeled_inputs) / len(inputs) * 100) if inputs else 100
        
        # ARIA attributes
        aria_elements = soup.find_all(attrs=lambda x: x and any(attr.startswith('aria-') for attr in x.keys()))
        
        # Color contrast (basic check)
        has_sufficient_contrast = True  # This would require more complex analysis
        
        return {
            "alt_text_percentage": round(alt_text_percentage, 2),
            "form_label_percentage": round(form_label_percentage, 2),
            "aria_elements_count": len(aria_elements),
            "has_sufficient_contrast": has_sufficient_contrast,
            "accessibility_score": round((alt_text_percentage + form_label_percentage) / 2, 2),
        }
    
    def _analyze_security(self, url: str, html: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Analyze security factors."""
        # HTTPS
        uses_https = url.startswith('https://')
        
        # Security headers (would be better analyzed from actual HTTP headers)
        has_csp = 'content-security-policy' in html.lower()
        has_frame_options = 'x-frame-options' in html.lower()
        has_xss_protection = 'x-xss-protection' in html.lower()
        
        # Mixed content
        http_links = soup.find_all(attrs={'src': lambda x: x and x.startswith('http:')})
        http_links.extend(soup.find_all(attrs={'href': lambda x: x and x.startswith('http:')}))
        has_mixed_content = len(http_links) > 0 and uses_https
        
        # External resources
        external_domains = set()
        for elem in soup.find_all(attrs={'src': True}):
            src = elem['src']
            if src.startswith('http'):
                domain = urlparse(src).netloc
                if domain != urlparse(url).netloc:
                    external_domains.add(domain)
        
        return {
            "uses_https": uses_https,
            "has_security_headers": has_csp or has_frame_options or has_xss_protection,
            "has_mixed_content": has_mixed_content,
            "external_domains_count": len(external_domains),
            "security_score": self._calculate_security_score(uses_https, has_csp, has_frame_options, has_mixed_content),
        }
    
    def _analyze_content_basic(self, content: str, html: str, soup: BeautifulSoup) -> Dict[str, Any]:
        """Basic content analysis for website analysis."""
        words = content.split()
        word_count = len(words)
        
        # Links and images
        links = soup.find_all('a', href=True)
        images = soup.find_all('img')
        
        # Reading time estimation (average 200 words per minute)
        reading_time_minutes = max(1, word_count // 200)
        
        return {
            "word_count": word_count,
            "link_count": len(links),
            "image_count": len(images),
            "reading_time_minutes": reading_time_minutes,
            "content_density": word_count / len(html) if html else 0,
        }
    
    def _generate_summary(self, content: str, sentences) -> str:
        """Generate a summary of the content."""
        if not sentences:
            return "No content to summarize."
        
        # Take first 3 sentences or 300 characters, whichever is shorter
        summary_sentences = []
        total_length = 0
        
        for sentence in sentences[:3]:
            sentence_text = str(sentence).strip()
            if total_length + len(sentence_text) > 300:
                break
            summary_sentences.append(sentence_text)
            total_length += len(sentence_text)
        
        summary = ' '.join(summary_sentences)
        return summary if summary else content[:300] + "..." if len(content) > 300 else content
    
    def _extract_key_topics(self, words) -> List[str]:
        """Extract key topics from words."""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'}
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            word_lower = word.lower()
            if len(word_lower) > 3 and word_lower not in stop_words and word_lower.isalpha():
                word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
        
        # Get top 10 words
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:10]]
    
    def _analyze_sentiment(self, blob: TextBlob) -> str:
        """Analyze sentiment of the content."""
        try:
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                return "positive"
            elif polarity < -0.1:
                return "negative"
            else:
                return "neutral"
        except:
            return "neutral"
    
    def _calculate_readability(self, words, sentences) -> float:
        """Calculate readability score (simplified Flesch Reading Ease)."""
        if not sentences or not words:
            return 0.0
        
        # Average sentence length
        avg_sentence_length = len(words) / len(sentences)
        
        # Estimate syllables (very simplified)
        total_syllables = sum(max(1, len(re.findall(r'[aeiouAEIOU]', str(word)))) for word in words)
        avg_syllables_per_word = total_syllables / len(words) if words else 0
        
        # Simplified Flesch Reading Ease formula
        score = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        return max(0, min(100, score))
    
    def _extract_entities(self, content: str) -> Dict[str, List[str]]:
        """Extract entities from content (simplified)."""
        # This is a very basic implementation
        # In production, you'd use spaCy or similar NLP libraries
        
        # Find capitalized words/phrases
        capitalized_pattern = r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b'
        capitalized_matches = re.findall(capitalized_pattern, content)
        
        # Find dates
        date_pattern = r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b|\b\d{4}-\d{2}-\d{2}\b'
        dates = re.findall(date_pattern, content)
        
        # Find email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, content)
        
        # Find URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, content)
        
        return {
            "people": capitalized_matches[:10],  # Simplified - would need NER
            "organizations": [],  # Would need proper NER
            "locations": [],  # Would need proper NER
            "dates": dates[:10],
            "emails": emails[:5],
            "urls": urls[:5],
        }
    
    def _calculate_security_score(self, uses_https: bool, has_csp: bool, has_frame_options: bool, has_mixed_content: bool) -> float:
        """Calculate a simple security score."""
        score = 0
        
        if uses_https:
            score += 40
        if has_csp:
            score += 20
        if has_frame_options:
            score += 20
        if not has_mixed_content:
            score += 20
        
        return score
    
    async def _load_cache(self):
        """Load analysis cache from file."""
        cache_file = os.path.join(self.cache_dir, "analysis_cache.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Reconstruct WebsiteAnalysis objects
                for domain, data in cache_data.items():
                    self.analysis_cache[domain] = WebsiteAnalysis(
                        domain=data["domain"],
                        url=data["url"],
                        title=data["title"],
                        description=data["description"],
                        technologies=data["technologies"],
                        performance=data["performance"],
                        seo=data["seo"],
                        accessibility=data["accessibility"],
                        security=data["security"],
                        content=data["content"],
                        timestamp=data["timestamp"],
                    )
            
            except Exception as e:
                logger.warning(f"Failed to load analysis cache: {e}")
    
    async def _save_cache(self):
        """Save analysis cache to file."""
        cache_file = os.path.join(self.cache_dir, "analysis_cache.json")
        try:
            cache_data = {domain: analysis.to_dict() for domain, analysis in self.analysis_cache.items()}
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        
        except Exception as e:
            logger.warning(f"Failed to save analysis cache: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        await self._save_cache()
        logger.info("Analysis service cleaned up")