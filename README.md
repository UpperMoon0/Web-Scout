# Web Scout MCP Server

A comprehensive Model Context Protocol (MCP) server for web scraping, searching, and analysis. This server provides AI assistants with powerful web intelligence capabilities through a standardized MCP interface.

## Features

### 🔍 Web Scraping
- **Multi-engine support**: HTTP requests and JavaScript-enabled scraping with Selenium
- **Content extraction**: Text, links, images, and metadata
- **Smart parsing**: BeautifulSoup-powered HTML analysis
- **Caching system**: Efficient content caching and history tracking

### 🌐 Web Search
- **Multiple search APIs**: Google Custom Search, Bing Search API
- **Search types**: Web, images, news, videos
- **Domain-specific search**: Search within specific websites
- **Fallback system**: Mock search when APIs are unavailable

### 📊 Website Analysis
- **SEO Analysis**: Title optimization, meta descriptions, heading structure
- **Performance Metrics**: Page size, resource counts, load estimations
- **Accessibility Audit**: Alt text, ARIA labels, form labels
- **Security Assessment**: HTTPS usage, security headers, mixed content
- **Technology Detection**: Frameworks, CMSs, analytics tools

### 📝 Content Analysis
- **Text Processing**: Summary generation, word counts, reading time
- **Sentiment Analysis**: Positive/negative/neutral classification
- **Entity Extraction**: People, organizations, dates, emails, URLs
- **Keyword Extraction**: Topic identification and frequency analysis
- **Readability Scoring**: Flesch Reading Ease calculation

### 📈 Website Monitoring
- **Change Detection**: Monitor websites for content changes
- **Configurable Intervals**: Custom check frequencies
- **History Tracking**: Maintain monitoring logs and statistics

## Installation

### Prerequisites
- Python 3.8 or higher
- Chrome/Chromium browser (for JavaScript scraping)
- ChromeDriver (automatically managed by Selenium)

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Development Installation
```bash
pip install -e .
```

## Configuration

### Environment Variables

Create a `.env` file or set environment variables:

```bash
# Required for enhanced search functionality (optional)
GOOGLE_API_KEY=your_google_api_key
GOOGLE_CSE_ID=your_custom_search_engine_id
BING_API_KEY=your_bing_search_api_key

# Server Configuration
WEB_SCOUT_USER_AGENT=Web-Scout-MCP/0.1.0
WEB_SCOUT_MAX_RETRIES=3
WEB_SCOUT_TIMEOUT=30
WEB_SCOUT_HEADLESS=true
WEB_SCOUT_CACHE_DIR=.web_scout_cache
WEB_SCOUT_LOG_LEVEL=INFO
WEB_SCOUT_ENV=production
```

### API Keys Setup

#### Google Custom Search API
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the Custom Search API
4. Create credentials (API key)
5. Set up a Custom Search Engine at [cse.google.com](https://cse.google.com/)

#### Bing Search API
1. Go to [Azure Portal](https://portal.azure.com/)
2. Create a Bing Search resource
3. Get your API key from the resource

## Usage

### Running the MCP Server

```bash
python -m src.server
```

### MCP Configuration

Add to your MCP settings file (e.g., `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "web-scout": {
      "command": "python",
      "args": ["-m", "src.server"],
      "cwd": "/path/to/web-scout",
      "env": {
        "WEB_SCOUT_USER_AGENT": "Web-Scout-MCP/0.1.0",
        "GOOGLE_API_KEY": "your_google_api_key",
        "GOOGLE_CSE_ID": "your_cse_id",
        "BING_API_KEY": "your_bing_api_key"
      }
    }
  }
}
```

## Available Tools

### `scrape_url`
Scrape content from a website.

**Parameters:**
- `url` (string, required): The URL to scrape
- `use_javascript` (boolean, optional): Use JavaScript rendering
- `extract_links` (boolean, optional): Extract all links
- `extract_images` (boolean, optional): Extract all images

### `search_web`
Search the web for information.

**Parameters:**
- `query` (string, required): Search query
- `max_results` (integer, optional): Maximum results to return
- `search_type` (string, optional): Type of search (web, images, news, videos)

### `analyze_website`
Perform comprehensive website analysis.

**Parameters:**
- `url` (string, required): Website URL to analyze
- `include_seo` (boolean, optional): Include SEO analysis
- `include_performance` (boolean, optional): Include performance analysis
- `include_accessibility` (boolean, optional): Include accessibility analysis
- `include_security` (boolean, optional): Include security analysis

### `analyze_content`
Analyze text content for insights.

**Parameters:**
- `content` (string, required): Text content to analyze
- `include_sentiment` (boolean, optional): Include sentiment analysis
- `include_entities` (boolean, optional): Include entity extraction
- `include_keywords` (boolean, optional): Include keyword extraction

### `search_domain`
Search within a specific domain.

**Parameters:**
- `domain` (string, required): Domain to search within
- `query` (string, required): Search query
- `max_results` (integer, optional): Maximum results to return

### `monitor_website`
Monitor a website for changes.

**Parameters:**
- `url` (string, required): URL to monitor
- `check_interval` (integer, optional): Check interval in minutes
- `notify_changes` (boolean, optional): Whether to notify about changes

## Available Resources

### Static Resources
- `webscout://history/scraping`: Scraping operation history
- `webscout://cache/analysis`: Cached analysis results

### Dynamic Resources
- `webscout://{domain}/analysis`: Analysis data for specific domain
- `webscout://{domain}/content`: Scraped content for specific domain

## Architecture

```
src/
├── __init__.py              # Package initialization
├── server.py                # Main MCP server implementation
├── config.py                # Configuration management
├── services/                # Core service modules
│   ├── __init__.py
│   ├── scraping_service.py  # Web scraping functionality
│   ├── search_service.py    # Search functionality
│   └── analysis_service.py  # Analysis functionality
└── tools/                   # MCP tool implementations
    ├── __init__.py
    └── web_scout_tools.py   # Tool handlers
```

## Development

### Project Structure
The project follows a modular architecture:

- **Services**: Core business logic for scraping, searching, and analysis
- **Tools**: MCP tool implementations that call services
- **Server**: MCP protocol handling and resource management
- **Config**: Environment-specific configuration management

### Running Tests
```bash
pytest tests/
```

### Code Formatting
```bash
black src/
flake8 src/
```

### Type Checking
```bash
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Troubleshooting

### Common Issues

1. **ChromeDriver not found**: Install ChromeDriver or ensure it's in your PATH
2. **Permission errors**: Check file permissions for cache directory
3. **API rate limits**: Implement delays between requests or upgrade API plans
4. **Memory issues**: Reduce max_content_length for large pages

### Debug Mode

Set environment variable for detailed logging:
```bash
WEB_SCOUT_LOG_LEVEL=DEBUG python -m src.server
```

## Support

For issues and questions:
- Create an issue on GitHub
- Check the documentation
- Review the troubleshooting section

## Roadmap

- [ ] Advanced NLP analysis with spaCy
- [ ] PDF and document scraping support
- [ ] Real-time website monitoring with webhooks
- [ ] Database storage for long-term caching
- [ ] API rate limiting and queuing system
- [ ] Distributed scraping with multiple workers
- [ ] Machine learning-based content classification