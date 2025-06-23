# Custom Search Engine Setup Guide

This guide provides step-by-step instructions for setting up and configuring the Web Scout custom search engine, allowing you to build your own free search index without relying on external APIs.

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Database Initialization](#database-initialization)
6. [Starting the Crawler](#starting-the-crawler)
7. [Performance Tuning](#performance-tuning)
8. [Monitoring and Maintenance](#monitoring-and-maintenance)
9. [Troubleshooting](#troubleshooting)

## Overview

The Web Scout custom search engine provides:

- **Local SQLite database** for storing crawled content
- **Intelligent web crawler** with robots.txt compliance
- **Full-text search** using SQLite FTS5
- **Content classification** (web, news, academic, reference)
- **Quality scoring** for ranking results
- **Image indexing** and search capabilities
- **Multi-threaded crawling** with rate limiting

### Architecture Components

```
Custom Search Engine
├── SQLite Database (web_scout_search.db)
│   ├── pages (main content)
│   ├── pages_fts (full-text search index)
│   ├── images (image metadata)
│   ├── links (link graph)
│   └── crawl_queue (pending URLs)
├── Web Crawler
│   ├── Robots.txt compliance
│   ├── Content classification
│   ├── Quality scoring
│   └── Link extraction
└── Search Interface
    ├── Web search
    ├── Image search
    └── News search
```

## Prerequisites

### System Requirements

- **Python 3.8+** (3.9+ recommended)
- **SQLite 3.35+** (for FTS5 support)
- **Memory**: Minimum 1GB RAM, 4GB+ recommended
- **Storage**: 1GB+ for database (grows with crawled content)
- **Network**: Stable internet connection for crawling

### Required Dependencies

```bash
# Core dependencies (automatically installed)
pip install -r requirements.txt
```

The custom search engine requires these additional packages:
- `scikit-learn>=1.3.0` - For TF-IDF vectorization and similarity
- `nltk>=3.8.0` - For text processing
- `whoosh>=2.7.4` - For advanced text analysis

## Installation

### 1. Clone and Install

```bash
# Navigate to the Web Scout server directory
cd Web-Scout-MCP-Server

# Install in development mode
pip install -e .
```

### 2. Download NLTK Data

The search engine automatically downloads required NLTK data on first run, but you can pre-download:

```bash
python -c "
import nltk
nltk.download('punkt')
nltk.download('stopwords')
"
```

### 3. Verify Installation

```bash
# Test the custom search engine
python test_custom_search.py
```

## Configuration

### Environment Variables

Create or update your `.env` file with custom search configuration:

```bash
# Custom Search Engine Configuration
CUSTOM_SEARCH_ENABLED=true
CUSTOM_SEARCH_DB=web_scout_search.db
CUSTOM_SEARCH_CRAWL_DELAY=1.0
CUSTOM_SEARCH_MAX_PAGES_PER_DOMAIN=1000
CUSTOM_SEARCH_MAX_CONTENT_LENGTH=1000000
CUSTOM_SEARCH_REQUEST_TIMEOUT=30
CUSTOM_SEARCH_USER_AGENT=Web-Scout-MCP/0.1.0

# Fallback Configuration
USE_CUSTOM_SEARCH_FIRST=true
FALLBACK_TO_EXTERNAL_APIS=true
```

### Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `CUSTOM_SEARCH_ENABLED` | `true` | Enable custom search engine |
| `CUSTOM_SEARCH_DB` | `web_scout_search.db` | Database file path |
| `CUSTOM_SEARCH_CRAWL_DELAY` | `1.0` | Delay between requests (seconds) |
| `CUSTOM_SEARCH_MAX_PAGES_PER_DOMAIN` | `1000` | Maximum pages per domain |
| `CUSTOM_SEARCH_MAX_CONTENT_LENGTH` | `1000000` | Maximum content size (bytes) |
| `CUSTOM_SEARCH_REQUEST_TIMEOUT` | `30` | HTTP request timeout (seconds) |
| `CUSTOM_SEARCH_USER_AGENT` | `Web-Scout-MCP/0.1.0` | User agent string |

### MCP Server Configuration

Add custom search configuration to your MCP settings:

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
        "CUSTOM_SEARCH_CRAWL_DELAY": "1.0",
        "USE_CUSTOM_SEARCH_FIRST": "true",
        "FALLBACK_TO_EXTERNAL_APIS": "true"
      }
    }
  }
}
```

## Database Initialization

The custom search engine automatically initializes its SQLite database on first run.

### Manual Database Setup

If you need to manually initialize or reset the database:

```python
# Initialize database manually
python -c "
import sys
sys.path.insert(0, 'src')
from services.custom_search_engine import CustomSearchEngine

engine = CustomSearchEngine('web_scout_search.db')
print('Database initialized successfully')
"
```

### Database Schema

The database includes these main tables:

- **pages**: Main content storage with FTS5 indexing
- **images**: Image metadata and search data
- **links**: Link graph for ranking and discovery
- **crawl_queue**: URLs pending crawling

## Starting the Crawler

### Automatic Crawling

The crawler starts automatically when the MCP server runs:

```bash
# Start MCP server (includes crawler)
python -m src.server
```

### Manual Crawling Control

For development or testing, you can control crawling manually:

```python
import asyncio
import sys
sys.path.insert(0, 'src')
from services.custom_search_engine import CustomSearchEngine

async def start_crawling():
    engine = CustomSearchEngine()
    await engine.initialize()
    
    # Crawler runs in background
    print("Crawler started...")
    await asyncio.sleep(60)  # Let it run for 1 minute
    
    # Check statistics
    stats = await engine.get_statistics()
    print(f"Pages crawled: {stats['total_pages']}")
    print(f"Domains: {stats['total_domains']}")
    
    await engine.cleanup()

asyncio.run(start_crawling())
```

### Seed URLs

The crawler starts with high-quality seed URLs:

- Wikipedia (reference content)
- BBC News, Reuters, Guardian (news content)
- Stack Overflow, GitHub (technical content)
- Educational institutions (.edu domains)
- Technical documentation sites

You can customize seed URLs by modifying [`CustomSearchEngine._get_seed_urls()`](src/services/custom_search_engine.py:177).

## Performance Tuning

### Crawling Performance

#### Adjust Crawl Rate

```bash
# Conservative (1 request per second)
CUSTOM_SEARCH_CRAWL_DELAY=1.0

# Moderate (2 requests per second)
CUSTOM_SEARCH_CRAWL_DELAY=0.5

# Aggressive (5 requests per second)
CUSTOM_SEARCH_CRAWL_DELAY=0.2
```

**Warning**: Aggressive crawling may trigger rate limiting or IP blocks.

#### Domain Limits

```bash
# Conservative
CUSTOM_SEARCH_MAX_PAGES_PER_DOMAIN=500

# Moderate
CUSTOM_SEARCH_MAX_PAGES_PER_DOMAIN=1000

# Extensive
CUSTOM_SEARCH_MAX_PAGES_PER_DOMAIN=5000
```

### Database Performance

#### Optimize SQLite Settings

The engine automatically configures SQLite for performance, but you can manually optimize:

```sql
-- Enable WAL mode for better concurrency
PRAGMA journal_mode=WAL;

-- Increase cache size (in KB)
PRAGMA cache_size=20000;

-- Optimize for speed over safety (use with caution)
PRAGMA synchronous=NORMAL;
PRAGMA temp_store=memory;
```

#### Database Maintenance

```python
# Optimize database periodically
import sqlite3

conn = sqlite3.connect('web_scout_search.db')
conn.execute('VACUUM;')
conn.execute('ANALYZE;')
conn.close()
```

### Memory Management

For large indexes, monitor memory usage:

```bash
# Limit content size per page
CUSTOM_SEARCH_MAX_CONTENT_LENGTH=500000  # 500KB instead of 1MB

# Reduce concurrent connections
# Modify aiohttp connector limit in CustomSearchEngine.__init__()
```

## Monitoring and Maintenance

### Search Statistics

Check crawler and search statistics:

```python
import asyncio
import sys
sys.path.insert(0, 'src')
from services.custom_search_engine import CustomSearchEngine

async def check_stats():
    engine = CustomSearchEngine()
    await engine.initialize()
    
    stats = await engine.get_statistics()
    print("=== Search Engine Statistics ===")
    print(f"Total pages: {stats['total_pages']:,}")
    print(f"Unique domains: {stats['total_domains']:,}")
    print(f"Total images: {stats['total_images']:,}")
    print("\nPages by type:")
    for content_type, count in stats['pages_by_type'].items():
        print(f"  {content_type}: {count:,}")
    print("\nCrawl queue status:")
    for status, count in stats['queue_by_status'].items():
        print(f"  {status}: {count:,}")
    
    await engine.cleanup()

asyncio.run(check_stats())
```

### Database Size Monitoring

```bash
# Check database file size
ls -lh web_scout_search.db

# Check detailed table sizes
sqlite3 web_scout_search.db "
SELECT 
    name,
    COUNT(*) as rows,
    ROUND(SUM(LENGTH(title) + LENGTH(content)) / 1024.0 / 1024.0, 2) as size_mb
FROM pages 
GROUP BY 'total'
UNION ALL
SELECT 
    'images' as name,
    COUNT(*) as rows,
    0 as size_mb
FROM images;
"
```

### Log Monitoring

Enable detailed logging for monitoring:

```bash
# Set log level for detailed crawler information
WEB_SCOUT_LOG_LEVEL=DEBUG python -m src.server
```

Common log patterns to monitor:
- `Successfully crawled: <URL>` - Successful page crawls
- `Failed to crawl <URL>: <error>` - Crawl failures
- `Database initialized successfully` - Startup confirmation
- `Adding seed URLs to crawl queue` - Initial setup

## Troubleshooting

### Common Issues

#### 1. No Search Results

**Symptoms**: Search queries return empty results

**Solutions**:
```bash
# Check if database has content
sqlite3 web_scout_search.db "SELECT COUNT(*) FROM pages;"

# Check if FTS index is populated
sqlite3 web_scout_search.db "SELECT COUNT(*) FROM pages_fts;"

# Rebuild FTS index if needed
sqlite3 web_scout_search.db "
INSERT INTO pages_fts(pages_fts) VALUES('rebuild');
"
```

#### 2. Crawler Not Working

**Symptoms**: No new pages being crawled

**Solutions**:
```python
# Check crawl queue status
import sqlite3
conn = sqlite3.connect('web_scout_search.db')
cursor = conn.cursor()
cursor.execute("SELECT status, COUNT(*) FROM crawl_queue GROUP BY status")
print(dict(cursor.fetchall()))
conn.close()

# Add URLs manually to queue
cursor.execute("INSERT INTO crawl_queue (url, domain, priority) VALUES (?, ?, ?)", 
               ('https://example.com', 'example.com', 5))
```

#### 3. High Memory Usage

**Symptoms**: Python process consuming excessive memory

**Solutions**:
- Reduce `CUSTOM_SEARCH_MAX_CONTENT_LENGTH`
- Lower `CUSTOM_SEARCH_MAX_PAGES_PER_DOMAIN`
- Restart the MCP server periodically
- Implement database cleanup for old content

#### 4. Slow Search Performance

**Symptoms**: Search queries taking too long

**Solutions**:
```sql
-- Rebuild search index
sqlite3 web_scout_search.db "
INSERT INTO pages_fts(pages_fts) VALUES('optimize');
"

-- Analyze query performance
sqlite3 web_scout_search.db "
EXPLAIN QUERY PLAN 
SELECT * FROM pages_fts WHERE pages_fts MATCH 'your query';
"
```

#### 5. Database Corruption

**Symptoms**: SQLite errors or inconsistent results

**Solutions**:
```bash
# Check database integrity
sqlite3 web_scout_search.db "PRAGMA integrity_check;"

# Repair if needed
sqlite3 web_scout_search.db "
PRAGMA journal_mode=DELETE;
VACUUM;
PRAGMA journal_mode=WAL;
"
```

### Getting Help

1. **Check Logs**: Enable DEBUG logging for detailed information
2. **Database Analysis**: Use SQLite tools to inspect database state
3. **Performance Monitoring**: Monitor CPU, memory, and disk usage
4. **Community Support**: Report issues with detailed logs and configuration

### Advanced Troubleshooting

#### Enable Crawler Debug Mode

```python
# Add debug logging to crawler
import logging
logging.getLogger('services.custom_search_engine').setLevel(logging.DEBUG)
```

#### Manual Database Inspection

```bash
# Interactive database exploration
sqlite3 web_scout_search.db

# Check recent crawl activity
.headers on
SELECT url, status, error_message, last_attempt 
FROM crawl_queue 
WHERE last_attempt > datetime('now', '-1 hour')
ORDER BY last_attempt DESC;

# Check content quality distribution
SELECT 
    ROUND(quality_score, 1) as quality,
    COUNT(*) as pages
FROM pages 
GROUP BY ROUND(quality_score, 1)
ORDER BY quality DESC;
```

## Next Steps

After successful setup:

1. **Let the crawler run** for several hours to build initial index
2. **Monitor performance** and adjust configuration as needed
3. **Test search functionality** with various queries
4. **Review migration guide** for switching from external APIs
5. **Set up monitoring** for production deployment

For production deployment, see the [Migration Guide](MIGRATION_GUIDE.md) for switching from external APIs to custom search.