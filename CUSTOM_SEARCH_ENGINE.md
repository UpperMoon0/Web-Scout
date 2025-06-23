# Web-Scout Custom Search Engine Architecture

## Executive Summary

This document outlines a comprehensive, scalable search engine architecture that replaces external API dependencies with a pure crawling approach. The system starts lightweight but scales horizontally as needs grow, maintaining the exact same public interface while providing relevant, ranked search results completely free of external API costs.

## Table of Contents

1. [System Architecture Overview](#system-architecture-overview)
2. [Database Schema & Storage Design](#database-schema--storage-design)
3. [Web Crawler & Indexer Architecture](#web-crawler--indexer-architecture)
4. [Search Algorithm & Ranking](#search-algorithm--ranking)
5. [Content Classification System](#content-classification-system)
6. [Implementation Phases](#implementation-phases)
7. [Performance & Resource Requirements](#performance--resource-requirements)
8. [Integration Plan](#integration-plan)
9. [Monitoring & Maintenance](#monitoring--maintenance)

## System Architecture Overview

```mermaid
graph TB
    subgraph "Public Interface Layer"
        SI[SearchService Interface]
        SM[search_web()]
        SD[search_domain()]
        SS[search_similar()]
    end
    
    subgraph "Search Engine Core"
        QP[Query Processor]
        SE[Search Engine]
        RR[Ranking & Relevance]
        CF[Content Filter]
    end
    
    subgraph "Data Storage Layer"
        IDX[Search Index]
        DB[(Content Database)]
        CACHE[(Query Cache)]
        META[(Metadata Store)]
    end
    
    subgraph "Crawling System"
        CS[Crawl Scheduler]
        WC[Web Crawler]
        CP[Content Processor]
        LD[Link Discovery]
    end
    
    subgraph "Content Processing"
        TE[Text Extraction]
        CE[Content Enrichment]
        IC[Image Classification]
        NC[News Classification]
    end
    
    SI --> QP
    QP --> SE
    SE --> IDX
    SE --> RR
    RR --> CF
    CF --> SI
    
    CS --> WC
    WC --> CP
    CP --> TE
    TE --> CE
    CE --> IC
    IC --> NC
    NC --> DB
    DB --> IDX
    
    WC --> LD
    LD --> CS
    
    SE --> CACHE
    SE --> META
```

### Architecture Principles

1. **Modularity**: Each component is independently scalable and replaceable
2. **Scalability**: Start with SQLite, migrate to PostgreSQL, then distributed systems
3. **Compatibility**: Maintain exact same API interface as current implementation
4. **Efficiency**: Optimize for both crawling speed and search performance
5. **Quality**: Implement multi-stage ranking for relevant results

## Database Schema & Storage Design

### Core Tables

#### Pages Table
Stores all crawled web pages with metadata and content.

```sql
CREATE TABLE pages (
    id BIGINT PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    domain VARCHAR(255) NOT NULL,
    title TEXT,
    content TEXT,
    html TEXT,
    content_hash VARCHAR(64),
    content_type VARCHAR(50) DEFAULT 'web',
    language VARCHAR(10),
    crawl_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_modified TIMESTAMP,
    page_rank DECIMAL(10,8) DEFAULT 0.0,
    quality_score DECIMAL(5,3) DEFAULT 0.0,
    status_code INTEGER,
    content_length INTEGER,
    INDEX idx_domain (domain),
    INDEX idx_content_type (content_type),
    INDEX idx_crawl_timestamp (crawl_timestamp),
    INDEX idx_page_rank (page_rank DESC),
    FULLTEXT INDEX idx_content_search (title, content)
);
```

#### Links Table
Stores link relationships for PageRank calculation and link analysis.

```sql
CREATE TABLE links (
    id BIGINT PRIMARY KEY,
    from_page_id BIGINT,
    to_page_id BIGINT,
    anchor_text TEXT,
    link_type VARCHAR(20) DEFAULT 'internal',
    discovered_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_page_id) REFERENCES pages(id),
    FOREIGN KEY (to_page_id) REFERENCES pages(id),
    INDEX idx_from_page (from_page_id),
    INDEX idx_to_page (to_page_id)
);
```

#### Search Index Table
Inverted index for fast text search with term frequency data.

```sql
CREATE TABLE search_index (
    id BIGINT PRIMARY KEY,
    term VARCHAR(255) NOT NULL,
    page_id BIGINT NOT NULL,
    term_frequency INTEGER DEFAULT 1,
    position_data JSON,
    field_type ENUM('title', 'content', 'meta', 'anchor') DEFAULT 'content',
    FOREIGN KEY (page_id) REFERENCES pages(id),
    INDEX idx_term (term),
    INDEX idx_page_term (page_id, term),
    INDEX idx_term_frequency (term, term_frequency DESC)
);
```

#### Images Table
For image search functionality.

```sql
CREATE TABLE images (
    id BIGINT PRIMARY KEY,
    page_id BIGINT,
    url TEXT NOT NULL,
    alt_text TEXT,
    title TEXT,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    content_type VARCHAR(50),
    discovered_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (page_id) REFERENCES pages(id),
    INDEX idx_page_id (page_id),
    INDEX idx_content_type (content_type)
);
```

#### Crawl Queue Table
Manages crawling scheduling and priority.

```sql
CREATE TABLE crawl_queue (
    id BIGINT PRIMARY KEY,
    url TEXT UNIQUE NOT NULL,
    domain VARCHAR(255),
    priority INTEGER DEFAULT 5,
    scheduled_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    retry_count INTEGER DEFAULT 0,
    last_attempt TIMESTAMP,
    status ENUM('pending', 'crawling', 'completed', 'failed') DEFAULT 'pending',
    error_message TEXT,
    INDEX idx_priority_schedule (priority DESC, scheduled_time),
    INDEX idx_domain (domain),
    INDEX idx_status (status)
);
```

### Scalability Strategy

- **Phase 1 (Current)**: SQLite with FTS5 for development and small-scale use
- **Phase 2 (Growth)**: PostgreSQL with full-text search extensions  
- **Phase 3 (Scale)**: Elasticsearch cluster with PostgreSQL for metadata

## Web Crawler & Indexer Architecture

### Crawler Design

```python
class DistributedCrawler:
    """Scalable web crawler with respectful crawling practices"""
    
    def __init__(self, config):
        self.respect_robots_txt = True
        self.crawl_delay = 1.0  # seconds between requests per domain
        self.max_concurrent_domains = 10
        self.max_concurrent_per_domain = 2
        self.domain_queues = {}
        self.rate_limiters = {}
    
    async def crawl_urls(self, urls: List[str]) -> List[CrawlResult]:
        """Crawl multiple URLs respecting rate limits and robots.txt"""
        # Implementation handles distributed crawling
        pass
    
    async def process_robots_txt(self, domain: str) -> RobotsTxt:
        """Parse and cache robots.txt for domain"""
        pass
    
    async def schedule_crawl(self, url: str, priority: int = 5):
        """Add URL to crawl queue with specified priority"""
        pass
```

### Seed Sites Strategy

#### Tier 1 - High Authority Sites (Initial Bootstrap)
- **Wikipedia**: All language versions for comprehensive knowledge base
- **Major News Sites**: BBC, Reuters, AP News, The Guardian
- **Educational Institutions**: .edu domains for academic content
- **Government Sites**: .gov domains for authoritative information
- **Technical Documentation**: Stack Overflow, GitHub, official docs

#### Tier 2 - General Content
- **Popular Blogs**: Medium, WordPress.com hosted blogs
- **E-commerce**: Product pages from major retailers
- **Reference Sites**: Dictionaries, encyclopedias, how-to guides
- **Forums**: Reddit public content, specialized forums

#### Tier 3 - Long Tail
- **Discovered Sites**: Sites found through link analysis
- **Domain-Specific**: Content based on search patterns
- **User-Submitted**: URLs submitted through the system
- **Social Discovery**: Links from social media platforms

### Content Processing Pipeline

```mermaid
graph LR
    URL[URL Queue] --> RC[Robots.txt Check]
    RC --> FETCH[HTTP Fetch]
    FETCH --> PARSE[HTML Parse]
    PARSE --> TEXT[Text Extract]
    TEXT --> LANG[Language Detect]
    LANG --> CLEAN[Content Clean]
    CLEAN --> CLASSIFY[Content Classify]
    CLASSIFY --> INDEX[Index Content]
    INDEX --> LINKS[Extract Links]
    LINKS --> QUEUE[Add to Queue]
```

#### Processing Steps

1. **URL Validation**: Check format, domain restrictions, duplicate detection
2. **Robots.txt Compliance**: Respect crawling permissions and delays
3. **Content Fetching**: HTTP requests with proper headers and user agent
4. **HTML Parsing**: Extract structured content using BeautifulSoup/lxml
5. **Text Extraction**: Clean HTML, extract readable text, preserve structure
6. **Language Detection**: Identify content language for appropriate indexing
7. **Content Classification**: Categorize as web, news, academic, etc.
8. **Link Discovery**: Extract and validate outbound links for crawling
9. **Indexing**: Store content in database and update search indexes

## Search Algorithm & Ranking

### Multi-Stage Ranking Algorithm

```python
class SearchRanker:
    """Multi-stage ranking algorithm for search results"""
    
    def calculate_relevance_score(self, query: str, page: Page) -> float:
        """Calculate comprehensive relevance score"""
        scores = {
            'text_similarity': self._text_similarity_score(query, page),
            'title_match': self._title_match_score(query, page),
            'page_rank': page.page_rank,
            'freshness': self._freshness_score(page),
            'quality': page.quality_score,
            'domain_authority': self._domain_authority_score(page.domain)
        }
        
        # Weighted combination
        final_score = (
            scores['text_similarity'] * 0.35 +
            scores['title_match'] * 0.25 +
            scores['page_rank'] * 0.15 +
            scores['freshness'] * 0.10 +
            scores['quality'] * 0.10 +
            scores['domain_authority'] * 0.05
        )
        
        return final_score
    
    def _text_similarity_score(self, query: str, page: Page) -> float:
        """Calculate text similarity using TF-IDF and cosine similarity"""
        # Implementation details for content matching
        pass
    
    def _title_match_score(self, query: str, page: Page) -> float:
        """Higher weight for title matches"""
        # Exact matches, partial matches, keyword presence
        pass
    
    def _freshness_score(self, page: Page) -> float:
        """Time-decay function for content freshness"""
        # More recent content scores higher
        pass
    
    def _domain_authority_score(self, domain: str) -> float:
        """Domain reputation and authority scoring"""
        # Based on link patterns, content quality, user behavior
        pass
```

### Search Types Implementation

#### Web Search
- **Full-text search** across all indexed content
- **Relevance ranking** using multi-factor algorithm
- **Query expansion** for better recall
- **Personalization** based on search history (optional)

#### Image Search
- **Alt text matching** for accessibility compliance
- **Surrounding content** analysis for context
- **Image metadata** (size, format, file name)
- **Visual similarity** (future enhancement with ML)

#### News Search
- **Time-sensitive ranking** prioritizing recent content
- **News domain identification** using domain patterns
- **Publication date** extraction and validation
- **Source credibility** scoring

#### Video Search
- **Embedded video detection** using iframe and object tags
- **Video platform** identification (YouTube, Vimeo, etc.)
- **Title and description** extraction from surrounding content
- **Duration and metadata** when available

### Domain-Specific Search Enhancement

```python
async def search_domain(self, domain: str, query: str) -> SearchResponse:
    """Enhanced domain search with domain-specific optimizations"""
    
    # Filter results to specific domain
    base_query = f"site:{domain} {query}"
    
    # Apply domain-specific ranking adjustments
    domain_context = await self._get_domain_context(domain)
    
    # Consider site structure and internal linking patterns
    site_structure = await self._analyze_site_structure(domain)
    
    # Execute search with domain-specific enhancements
    results = await self._execute_domain_search(base_query, domain_context, site_structure)
    
    return results
```

## Content Classification System

### Automated Classification

```python
class ContentClassifier:
    """Classifies content into different types and categories"""
    
    def classify_content_type(self, page: Page) -> str:
        """Classify content into primary type categories"""
        
        # News classification
        if self._is_news_content(page):
            return 'news'
        
        # Academic content
        if self._is_academic_content(page):
            return 'academic'
        
        # E-commerce
        if self._is_ecommerce_content(page):
            return 'shopping'
        
        # Reference material
        if self._is_reference_content(page):
            return 'reference'
            
        return 'web'
    
    def _is_news_content(self, page: Page) -> bool:
        """Detect news content using multiple signals"""
        news_indicators = [
            page.domain in self.news_domains,
            self._has_publication_date(page),
            self._has_news_keywords(page),
            self._has_author_byline(page),
            self._has_news_structure(page.html)
        ]
        return sum(news_indicators) >= 3
    
    def _is_academic_content(self, page: Page) -> bool:
        """Identify academic and educational content"""
        academic_indicators = [
            page.domain.endswith('.edu'),
            self._has_academic_keywords(page),
            self._has_citation_format(page),
            self._has_research_structure(page)
        ]
        return sum(academic_indicators) >= 2
    
    def _is_ecommerce_content(self, page: Page) -> bool:
        """Detect e-commerce and shopping content"""
        commerce_indicators = [
            self._has_price_indicators(page),
            self._has_product_schema(page.html),
            self._has_shopping_keywords(page),
            self._has_cart_functionality(page.html)
        ]
        return sum(commerce_indicators) >= 2
```

### Quality Assessment

```python
def calculate_quality_score(self, page: Page) -> float:
    """Calculate comprehensive content quality score"""
    factors = {
        'content_length': self._content_length_score(page),
        'readability': self._readability_score(page.content),
        'structure': self._html_structure_score(page.html),
        'external_links': self._external_links_score(page),
        'grammar': self._grammar_score(page.content),
        'uniqueness': self._uniqueness_score(page.content),
        'multimedia': self._multimedia_score(page),
        'metadata': self._metadata_completeness_score(page)
    }
    
    # Weighted average of quality factors
    weights = {
        'content_length': 0.15,
        'readability': 0.20,
        'structure': 0.15,
        'external_links': 0.10,
        'grammar': 0.15,
        'uniqueness': 0.15,
        'multimedia': 0.05,
        'metadata': 0.05
    }
    
    quality_score = sum(factors[key] * weights[key] for key in factors)
    return min(max(quality_score, 0.0), 1.0)
```

## Implementation Phases

### Phase 1: Foundation (Weeks 1-4)

#### Week 1: Database and Core Infrastructure
- [ ] Implement SQLite schema with FTS5 full-text search
- [ ] Create database abstraction layer for future migrations
- [ ] Set up basic CRUD operations for pages and links
- [ ] Implement query caching system

#### Week 2: Basic Crawler
- [ ] Build HTTP crawler with robots.txt respect
- [ ] Implement content extraction and cleaning
- [ ] Add basic link discovery and URL validation
- [ ] Create crawl queue management system

#### Week 3: Search Interface Integration
- [ ] Replace [`_search_google()`](Web-Scout-MCP-Server/src/services/search_service.py:191), [`_search_bing()`](Web-Scout-MCP-Server/src/services/search_service.py:235), [`_search_fallback()`](Web-Scout-MCP-Server/src/services/search_service.py:310) methods
- [ ] Implement basic text search using FTS5
- [ ] Ensure results return in existing [`SearchResponse`](Web-Scout-MCP-Server/src/services/search_service.py:53) format
- [ ] Add search result ranking (basic TF-IDF)

#### Week 4: Basic Content Processing
- [ ] Implement content classification (web, news, academic)
- [ ] Add language detection for content
- [ ] Create basic quality scoring algorithm
- [ ] Set up initial seed site crawling

### Phase 2: Enhancement (Weeks 5-8)

#### Week 5: Advanced Ranking
- [ ] Implement PageRank calculation algorithm
- [ ] Add domain authority scoring
- [ ] Enhance content quality assessment
- [ ] Create relevance scoring combination algorithm

#### Week 6: Content Classification
- [ ] Improve news detection and classification
- [ ] Add image content handling and metadata extraction
- [ ] Implement e-commerce content detection
- [ ] Create content type categorization system

#### Week 7: Search Type Specialization
- [ ] Implement image search functionality
- [ ] Add news search with time-sensitive ranking
- [ ] Create video search capabilities
- [ ] Enhance domain-specific search features

#### Week 8: Performance Optimization
- [ ] Optimize database queries and indexing
- [ ] Implement advanced caching strategies
- [ ] Add search result personalization (optional)
- [ ] Performance testing and bottleneck identification

### Phase 3: Scaling (Weeks 9-12)

#### Week 9: Database Scaling
- [ ] Migrate from SQLite to PostgreSQL
- [ ] Implement database sharding strategy
- [ ] Add read replicas for search queries
- [ ] Optimize database schema for scale

#### Week 10: Distributed Crawling
- [ ] Implement distributed crawler architecture
- [ ] Add crawler load balancing
- [ ] Create crawl coordination system
- [ ] Implement real-time crawling capabilities

#### Week 11: Advanced Features
- [ ] Implement similar page discovery algorithm
- [ ] Add machine learning ranking features
- [ ] Create automated quality assessment
- [ ] Implement user behavior tracking (optional)

#### Week 12: Production Readiness
- [ ] Add comprehensive monitoring and logging
- [ ] Implement backup and disaster recovery
- [ ] Create deployment automation
- [ ] Performance testing and optimization

## Performance & Resource Requirements

### Initial Resource Requirements (Phase 1)

#### Hardware Requirements
- **Storage**: 10-50GB for initial index
- **Memory**: 2-4GB RAM for basic operations
- **CPU**: 2-4 cores for crawling and indexing
- **Network**: Moderate bandwidth for respectful crawling

#### Software Dependencies
- **Database**: SQLite 3.35+ with FTS5 extension
- **Python**: 3.9+ with asyncio support
- **Libraries**: aiohttp, BeautifulSoup4, nltk, scikit-learn
- **Optional**: Redis for caching, Celery for task queuing

### Scaling Projections

| Scale | Pages Indexed | Storage | Memory | Architecture |
|-------|---------------|---------|--------|--------------|
| Small | 100K pages | ~5GB | 2GB RAM | Single SQLite |
| Medium | 1M pages | ~50GB | 4GB RAM | PostgreSQL |
| Large | 10M pages | ~500GB | 8GB RAM | Distributed setup |
| Enterprise | 100M+ pages | ~5TB | 32GB+ RAM | Elasticsearch cluster |

### Performance Targets

#### Search Performance
- **Response Time**: <500ms for typical queries
- **Throughput**: 100+ queries per second
- **Availability**: 99.9% uptime target
- **Cache Hit Rate**: >80% for common queries

#### Crawling Performance
- **Crawl Rate**: 100-1000 pages/hour (respecting rate limits)
- **Success Rate**: >95% successful crawl attempts
- **Coverage**: 1M+ unique pages within 6 months
- **Freshness**: Daily updates for news content

#### Index Performance
- **Update Latency**: <1 hour for new content to appear in search
- **Ranking Updates**: Real-time for new content, hourly for ranking scores
- **Index Size**: <10% of total content size
- **Compression**: 70%+ compression ratio for stored content

## Integration Plan

### Backward Compatibility

The new system maintains complete compatibility with existing interfaces:

```python
# Existing SearchService methods preserved exactly
async def search_web(
    self, 
    query: str, 
    max_results: int = 10, 
    search_type: str = "web"
) -> SearchResponse:
    """Maintains exact same signature and return format"""
    pass

async def search_domain(
    self, 
    domain: str, 
    query: str, 
    max_results: int = 10
) -> SearchResponse:
    """No changes to public interface"""
    pass

async def search_similar(
    self, 
    url: str, 
    max_results: int = 10
) -> SearchResponse:
    """Compatible with existing similar search functionality"""
    pass
```

### Migration Strategy

#### Phase 1: Parallel Implementation
1. **New Methods**: Implement custom search methods alongside existing ones
2. **Feature Flags**: Use configuration to switch between old and new systems
3. **A/B Testing**: Compare results quality between systems
4. **Fallback Support**: Maintain external API fallback during transition

#### Phase 2: Gradual Cutover
1. **Internal Testing**: Use custom search for internal queries first
2. **Selective Routing**: Route specific query types to custom search
3. **Quality Monitoring**: Compare result relevance and user satisfaction
4. **Performance Validation**: Ensure response times meet requirements

#### Phase 3: Full Migration
1. **Complete Cutover**: Switch all search traffic to custom engine
2. **External API Removal**: Remove external API dependencies
3. **Cache Migration**: Preserve existing search cache format and data
4. **Documentation Update**: Update API documentation and examples

### Cache Migration

```python
class CacheMigration:
    """Handles migration of existing search cache to new format"""
    
    async def migrate_existing_cache(self):
        """Convert existing cache entries to new format"""
        # Load existing cache from search_cache.json
        # Convert SearchResponse objects to new internal format
        # Preserve cache keys and expiration times
        pass
    
    async def validate_cache_compatibility(self):
        """Ensure cache format compatibility"""
        # Verify SearchResponse format compatibility
        # Check timestamp and metadata preservation
        pass
```

## Monitoring & Maintenance

### Health Metrics

#### Crawling Metrics
- **Crawl Success Rate**: Percentage of successful crawl attempts
- **Error Rate by Domain**: Track which domains have crawling issues
- **Robots.txt Compliance**: Ensure respectful crawling practices
- **Queue Depth**: Monitor crawl queue size and processing rate
- **Content Freshness**: Track how recent indexed content is

#### Search Metrics
- **Query Response Time**: Track search performance over time
- **Result Relevance**: Monitor click-through rates and user feedback
- **Cache Hit Rate**: Optimize caching for common queries
- **Query Volume**: Track search traffic patterns
- **Error Rate**: Monitor search failures and their causes

#### System Metrics
- **Database Performance**: Query execution times and lock contention
- **Storage Usage**: Track index growth and storage efficiency
- **Memory Usage**: Monitor memory consumption patterns
- **CPU Utilization**: Track processing load during crawling and searching

### Maintenance Tasks

#### Daily Maintenance
- [ ] Monitor crawl queue health and error rates
- [ ] Check search response times and availability
- [ ] Review storage usage and capacity planning
- [ ] Validate backup processes and data integrity

#### Weekly Maintenance
- [ ] Optimize database indexes and query performance
- [ ] Clean duplicate content and dead links
- [ ] Review and update seed site lists
- [ ] Analyze search quality and user feedback

#### Monthly Maintenance
- [ ] Recalculate PageRank and authority scores
- [ ] Update content quality assessment algorithms
- [ ] Review and optimize crawling patterns
- [ ] Plan capacity expansion and resource allocation

#### Quarterly Maintenance
- [ ] Evaluate and update ranking algorithms
- [ ] Review and expand seed site coverage
- [ ] Assess system architecture and scaling needs
- [ ] Update security measures and access controls

### Alerting and Monitoring Setup

```python
class SearchEngineMonitoring:
    """Comprehensive monitoring for search engine health"""
    
    def setup_alerts(self):
        """Configure alerting for critical metrics"""
        alerts = {
            'crawl_success_rate': {'threshold': 0.90, 'severity': 'warning'},
            'search_response_time': {'threshold': 1000, 'severity': 'critical'},
            'storage_usage': {'threshold': 0.85, 'severity': 'warning'},
            'error_rate': {'threshold': 0.05, 'severity': 'critical'}
        }
        
    def generate_health_report(self):
        """Generate comprehensive system health report"""
        # Crawling health metrics
        # Search performance metrics
        # Resource utilization metrics
        # Quality assessment metrics
        pass
```

## Conclusion

This architecture provides a robust foundation for a custom search engine that:

1. **Maintains Compatibility**: Preserves existing API interfaces
2. **Scales Gradually**: Starts simple, grows with requirements
3. **Ensures Quality**: Implements comprehensive ranking and quality assessment
4. **Operates Independently**: No external API dependencies or costs
5. **Enables Growth**: Modular design supports feature expansion

The phased implementation approach allows for incremental development and testing, while the scalable architecture ensures the system can grow from thousands to millions of indexed pages as needed.

### Next Steps

1. **Review Architecture**: Validate the design meets your requirements
2. **Setup Development Environment**: Prepare infrastructure for implementation
3. **Begin Phase 1**: Start with foundation components and basic functionality
4. **Monitor Progress**: Track implementation against timeline and quality metrics
5. **Plan Scaling**: Prepare for growth and additional feature requirements

This comprehensive architecture document serves as both a technical specification and implementation guide for building a world-class search engine tailored to your specific needs.