# Migration Guide: External APIs to Custom Search

This guide explains how to migrate from external search APIs (Google Custom Search, Bing) to the custom search engine, including configuration changes, testing procedures, and fallback strategies.

## Table of Contents

1. [Migration Overview](#migration-overview)
2. [Pre-Migration Assessment](#pre-migration-assessment)
3. [Configuration Changes](#configuration-changes)
4. [Migration Strategies](#migration-strategies)
5. [Testing and Validation](#testing-and-validation)
6. [Fallback Configuration](#fallback-configuration)
7. [Performance Comparison](#performance-comparison)
8. [Troubleshooting Migration Issues](#troubleshooting-migration-issues)

## Migration Overview

### Why Migrate to Custom Search?

**Benefits:**
- **Zero API costs** - No usage limits or billing
- **Complete control** - Customize crawling and ranking
- **Privacy** - No data sent to external services
- **Reliability** - No API key expiration or service outages
- **Customization** - Tailor search results to your needs

**Trade-offs:**
- **Initial setup time** - Requires database initialization and crawling
- **Resource usage** - Uses local storage and processing power
- **Coverage limitations** - Limited to crawled content
- **Maintenance** - Requires ongoing database management

### Migration Timeline

```
Phase 1: Preparation (1-2 hours)
├── Install custom search dependencies
├── Configure environment variables
└── Initialize database

Phase 2: Parallel Operation (1-7 days)
├── Enable custom search alongside external APIs
├── Build search index through crawling
└── Test and compare results

Phase 3: Full Migration (immediate)
├── Disable external APIs
├── Enable custom search as primary
└── Configure fallback if needed
```

## Pre-Migration Assessment

### Current API Usage Analysis

Before migrating, assess your current external API usage:

```python
# Check current search configuration
import os
from dotenv import load_dotenv

load_dotenv()

print("=== Current Search Configuration ===")
print(f"Google API Key: {'SET' if os.getenv('GOOGLE_API_KEY') else 'NOT SET'}")
print(f"Google CSE ID: {'SET' if os.getenv('GOOGLE_CSE_ID') else 'NOT SET'}")
print(f"Bing API Key: {'SET' if os.getenv('BING_API_KEY') else 'NOT SET'}")
print(f"Custom Search Enabled: {os.getenv('CUSTOM_SEARCH_ENABLED', 'false')}")
```

### Resource Requirements Assessment

Estimate resource needs based on expected usage:

| Usage Level | Daily Searches | Storage Need | Memory Rec. | CPU Rec. |
|-------------|----------------|--------------|-------------|----------|
| Light | <100 | 500MB | 1GB RAM | 1 CPU core |
| Moderate | 100-1000 | 2GB | 2GB RAM | 2 CPU cores |
| Heavy | 1000+ | 5GB+ | 4GB+ RAM | 4+ CPU cores |

### Test External API Performance

Document current performance for comparison:

```python
# Benchmark current external APIs
import asyncio
import time
import sys
sys.path.insert(0, 'src')
from services.search_service import SearchService

async def benchmark_external():
    # Test with external APIs only
    config = {
        'use_custom_search': False,
        'fallback_to_external_apis': True
    }
    
    service = SearchService(config)
    await service.initialize()
    
    test_queries = ["python programming", "machine learning", "web development"]
    
    print("=== External API Benchmark ===")
    for query in test_queries:
        start_time = time.time()
        result = await service.search_web(query, max_results=10)
        duration = time.time() - start_time
        
        print(f"Query: '{query}'")
        print(f"  Results: {len(result.results)}")
        print(f"  Time: {duration:.2f}s")
        print(f"  Source: {result.results[0].source if result.results else 'None'}")
        print()
    
    await service.cleanup()

# Run benchmark
asyncio.run(benchmark_external())
```

## Configuration Changes

### Step 1: Update Environment Variables

Create or update your `.env` file with custom search configuration:

```bash
# =============================================================================
# CUSTOM SEARCH ENGINE CONFIGURATION
# =============================================================================

# Enable custom search engine
CUSTOM_SEARCH_ENABLED=true

# Database configuration
CUSTOM_SEARCH_DB=web_scout_search.db

# Crawler settings
CUSTOM_SEARCH_CRAWL_DELAY=1.0
CUSTOM_SEARCH_MAX_PAGES_PER_DOMAIN=1000
CUSTOM_SEARCH_MAX_CONTENT_LENGTH=1000000
CUSTOM_SEARCH_REQUEST_TIMEOUT=30
CUSTOM_SEARCH_USER_AGENT=Web-Scout-MCP/0.1.0

# Search behavior
USE_CUSTOM_SEARCH_FIRST=true
FALLBACK_TO_EXTERNAL_APIS=true  # Keep true during migration

# =============================================================================
# EXTERNAL API CONFIGURATION (Keep for fallback)
# =============================================================================

# Google Custom Search (keep for fallback)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_CSE_ID=your_custom_search_engine_id_here

# Bing Search API (keep for fallback)
BING_API_KEY=your_bing_search_api_key_here

# =============================================================================
# GENERAL CONFIGURATION
# =============================================================================

WEB_SCOUT_USER_AGENT=Web-Scout-MCP/0.1.0
WEB_SCOUT_MAX_RETRIES=3
WEB_SCOUT_TIMEOUT=30
WEB_SCOUT_HEADLESS=true
WEB_SCOUT_CACHE_DIR=.web_scout_cache
WEB_SCOUT_LOG_LEVEL=INFO
WEB_SCOUT_ENV=production
```

### Step 2: Update MCP Server Configuration

Modify your MCP settings (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "web-scout": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/Web-Scout-MCP-Server",
      "env": {
        "CUSTOM_SEARCH_ENABLED": "true",
        "CUSTOM_SEARCH_DB": "web_scout_search.db",
        "USE_CUSTOM_SEARCH_FIRST": "true",
        "FALLBACK_TO_EXTERNAL_APIS": "true",
        "WEB_SCOUT_LOG_LEVEL": "INFO"
      }
    }
  }
}
```

### Step 3: Verify Configuration

Test that configuration is properly loaded:

```python
# Verify custom search configuration
import sys
sys.path.insert(0, 'src')
from config import Config

config = Config()
print("=== Custom Search Configuration ===")
print(f"Enabled: {config.custom_search_enabled}")
print(f"Database: {config.custom_search_db}")
print(f"Use Custom First: {config.use_custom_search_first}")
print(f"Fallback Enabled: {config.fallback_to_external_apis}")
```

## Migration Strategies

### Strategy 1: Gradual Migration (Recommended)

This approach enables custom search alongside external APIs, gradually building confidence:

**Week 1: Parallel Operation**
```bash
CUSTOM_SEARCH_ENABLED=true
USE_CUSTOM_SEARCH_FIRST=true
FALLBACK_TO_EXTERNAL_APIS=true
```

**Week 2: Primary Custom Search**
```bash
CUSTOM_SEARCH_ENABLED=true
USE_CUSTOM_SEARCH_FIRST=true
FALLBACK_TO_EXTERNAL_APIS=true  # Keep for edge cases
```

**Week 3+: Custom Search Only**
```bash
CUSTOM_SEARCH_ENABLED=true
USE_CUSTOM_SEARCH_FIRST=true
FALLBACK_TO_EXTERNAL_APIS=false  # Disable external APIs
```

### Strategy 2: Immediate Migration

For scenarios where external API costs need immediate elimination:

```bash
# Complete switch to custom search
CUSTOM_SEARCH_ENABLED=true
USE_CUSTOM_SEARCH_FIRST=true
FALLBACK_TO_EXTERNAL_APIS=false

# Remove API keys to prevent usage
# GOOGLE_API_KEY=  # Comment out
# BING_API_KEY=    # Comment out
```

### Strategy 3: Domain-Specific Migration

Migrate specific domains or query types first:

```python
# Custom implementation for domain-specific migration
async def domain_specific_search(query: str, domain: str = None):
    if domain and domain in ['technical', 'programming', 'documentation']:
        # Use custom search for technical content
        result = await custom_search_engine.search(query)
    else:
        # Use external APIs for general content
        result = await external_api_search(query)
    
    return result
```

## Testing and Validation

### Functional Testing

Create comprehensive tests to validate custom search functionality:

```python
# Test script: test_migration.py
import asyncio
import sys
sys.path.insert(0, 'src')
from services.search_service import SearchService

async def test_migration():
    """Test both external and custom search implementations."""
    
    test_cases = [
        # General queries
        "python programming tutorial",
        "machine learning algorithms", 
        "web development best practices",
        
        # News queries
        "latest technology news",
        "climate change updates",
        
        # Technical queries
        "REST API design patterns",
        "database optimization techniques",
        
        # Image queries
        "python logo",
        "data visualization charts"
    ]
    
    print("=== Migration Testing ===\n")
    
    for search_type in ['web', 'images', 'news']:
        print(f"Testing {search_type.upper()} search:")
        print("-" * 40)
        
        for query in test_cases[:3]:  # Test first 3 queries per type
            # Test custom search
            config_custom = {
                'use_custom_search': True,
                'fallback_to_external_apis': False
            }
            service_custom = SearchService(config_custom)
            await service_custom.initialize()
            
            try:
                result_custom = await service_custom.search_web(
                    query, max_results=5, search_type=search_type
                )
                custom_count = len(result_custom.results)
            except Exception as e:
                custom_count = f"Error: {e}"
            
            await service_custom.cleanup()
            
            # Test external APIs
            config_external = {
                'use_custom_search': False,
                'fallback_to_external_apis': True
            }
            service_external = SearchService(config_external)
            await service_external.initialize()
            
            try:
                result_external = await service_external.search_web(
                    query, max_results=5, search_type=search_type
                )
                external_count = len(result_external.results)
            except Exception as e:
                external_count = f"Error: {e}"
            
            await service_external.cleanup()
            
            print(f"  '{query}':")
            print(f"    Custom: {custom_count} results")
            print(f"    External: {external_count} results")
            print()
        
        print()

# Run migration test
asyncio.run(test_migration())
```

### Performance Testing

Compare response times and result quality:

```python
# Performance comparison script
import asyncio
import time
import statistics
import sys
sys.path.insert(0, 'src')
from services.search_service import SearchService

async def performance_comparison():
    """Compare performance between custom and external search."""
    
    queries = [
        "artificial intelligence",
        "web development",
        "data science",
        "cloud computing",
        "cybersecurity"
    ]
    
    custom_times = []
    external_times = []
    
    print("=== Performance Comparison ===\n")
    
    for query in queries:
        print(f"Testing: '{query}'")
        
        # Test custom search
        config = {'use_custom_search': True, 'fallback_to_external_apis': False}
        service = SearchService(config)
        await service.initialize()
        
        start_time = time.time()
        try:
            result = await service.search_web(query, max_results=10)
            custom_time = time.time() - start_time
            custom_times.append(custom_time)
            custom_results = len(result.results)
        except Exception as e:
            custom_time = None
            custom_results = f"Error: {e}"
        
        await service.cleanup()
        
        # Test external APIs
        config = {'use_custom_search': False, 'fallback_to_external_apis': True}
        service = SearchService(config)
        await service.initialize()
        
        start_time = time.time()
        try:
            result = await service.search_web(query, max_results=10)
            external_time = time.time() - start_time
            external_times.append(external_time)
            external_results = len(result.results)
        except Exception as e:
            external_time = None
            external_results = f"Error: {e}"
        
        await service.cleanup()
        
        print(f"  Custom: {custom_time:.2f}s ({custom_results} results)")
        print(f"  External: {external_time:.2f}s ({external_results} results)")
        print()
    
    # Summary statistics
    if custom_times and external_times:
        print("=== Performance Summary ===")
        print(f"Custom Search:")
        print(f"  Average: {statistics.mean(custom_times):.2f}s")
        print(f"  Median: {statistics.median(custom_times):.2f}s")
        print(f"  Min: {min(custom_times):.2f}s")
        print(f"  Max: {max(custom_times):.2f}s")
        print()
        print(f"External APIs:")
        print(f"  Average: {statistics.mean(external_times):.2f}s")
        print(f"  Median: {statistics.median(external_times):.2f}s")
        print(f"  Min: {min(external_times):.2f}s")
        print(f"  Max: {max(external_times):.2f}s")

# Run performance test
asyncio.run(performance_comparison())
```

## Fallback Configuration

### Intelligent Fallback Strategy

Configure smart fallback that uses external APIs only when needed:

```python
# Enhanced fallback configuration in search_service.py
class SearchService:
    async def search_web(self, query: str, **kwargs):
        # Try custom search first
        if self.config.use_custom_search_first:
            try:
                result = await self.custom_search_engine.search(query, **kwargs)
                
                # Check if results are sufficient
                if len(result.results) >= self.config.min_results_threshold:
                    return result
                
                # If insufficient results and fallback enabled
                if self.config.fallback_to_external_apis:
                    external_result = await self._search_external_apis(query, **kwargs)
                    
                    # Combine results
                    combined_results = result.results + external_result.results
                    result.results = combined_results[:kwargs.get('max_results', 10)]
                    result.total_results = len(combined_results)
                    
                return result
                
            except Exception as e:
                if self.config.fallback_to_external_apis:
                    return await self._search_external_apis(query, **kwargs)
                raise e
        
        # External APIs as primary
        return await self._search_external_apis(query, **kwargs)
```

### Fallback Configuration Options

```bash
# Fallback behavior settings
MIN_RESULTS_THRESHOLD=3           # Minimum results before fallback
FALLBACK_ON_ERROR=true           # Fallback on custom search errors
COMBINE_RESULTS=true             # Combine custom and external results
MAX_FALLBACK_RESULTS=5           # Limit external results when combining
FALLBACK_TIMEOUT=10              # Timeout for fallback requests
```

### Query-Type Specific Fallback

```bash
# Configure fallback by search type
FALLBACK_WEB_SEARCH=true         # Allow fallback for web search
FALLBACK_IMAGE_SEARCH=false      # No fallback for images (custom only)
FALLBACK_NEWS_SEARCH=true        # Allow fallback for news
```

## Performance Comparison

### Expected Performance Characteristics

| Metric | Custom Search | External APIs | Notes |
|--------|---------------|---------------|-------|
| **Response Time** | 50-200ms | 200-1000ms | Custom is typically faster |
| **Throughput** | 50+ queries/sec | 10-100 queries/sec | Limited by API rate limits |
| **Availability** | 99.9%+ | 99.5% | Depends on API provider SLA |
| **Cost** | $0 | $5-50/1000 queries | Variable by provider |
| **Latency** | <100ms | 200-500ms | Network overhead for APIs |

### Quality Comparison Metrics

Track these metrics during migration:

```python
# Quality tracking script
def track_search_quality(query: str, custom_results, external_results):
    """Track and compare search result quality."""
    
    metrics = {
        'query': query,
        'custom': {
            'result_count': len(custom_results),
            'avg_snippet_length': sum(len(r.snippet) for r in custom_results) / len(custom_results) if custom_results else 0,
            'unique_domains': len(set(urlparse(r.url).netloc for r in custom_results)),
            'has_thumbnails': sum(1 for r in custom_results if r.thumbnail),
        },
        'external': {
            'result_count': len(external_results), 
            'avg_snippet_length': sum(len(r.snippet) for r in external_results) / len(external_results) if external_results else 0,
            'unique_domains': len(set(urlparse(r.url).netloc for r in external_results)),
            'has_thumbnails': sum(1 for r in external_results if r.thumbnail),
        }
    }
    
    return metrics
```

## Troubleshooting Migration Issues

### Common Migration Problems

#### 1. Empty Custom Search Results

