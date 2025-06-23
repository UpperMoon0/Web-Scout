#!/usr/bin/env python3
"""
Web Scout MCP Server

A Model Context Protocol server providing web scraping, searching, and analysis tools.
"""

import asyncio
import logging
import os
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    ResourceTemplate,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)

from .services.scraping_service import ScrapingService
from .services.search_service import SearchService
from .services.analysis_service import AnalysisService
from .tools.web_scout_tools import WebScoutTools

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Server configuration
SERVER_NAME = "web-scout-server"
SERVER_VERSION = "0.1.0"

# Environment configuration
config = {
    "user_agent": os.getenv("WEB_SCOUT_USER_AGENT", "Web-Scout-MCP/0.1.0"),
    "max_retries": int(os.getenv("WEB_SCOUT_MAX_RETRIES", "3")),
    "timeout": int(os.getenv("WEB_SCOUT_TIMEOUT", "30")),
    "enable_headless": os.getenv("WEB_SCOUT_HEADLESS", "true").lower() != "false",
    "cache_dir": os.getenv("WEB_SCOUT_CACHE_DIR", ".web_scout_cache"),
}

# Initialize services
scraping_service = ScrapingService(config)
search_service = SearchService(config)
analysis_service = AnalysisService(config)

# Create MCP server
server = Server(SERVER_NAME)


@server.list_resources()
async def list_resources() -> List[Resource]:
    """List available resources."""
    return [
        Resource(
            uri="webscout://history/scraping",
            name="Scraping History",
            description="History of web scraping operations",
            mimeType="application/json",
        ),
        Resource(
            uri="webscout://cache/analysis",
            name="Analysis Cache",
            description="Cached website analysis results",
            mimeType="application/json",
        ),
    ]


@server.list_resource_templates()
async def list_resource_templates() -> List[ResourceTemplate]:
    """List available resource templates."""
    return [
        ResourceTemplate(
            uriTemplate="webscout://{domain}/analysis",
            name="Website Analysis",
            description="Analysis data for a specific domain",
            mimeType="application/json",
        ),
        ResourceTemplate(
            uriTemplate="webscout://{domain}/content",
            name="Website Content",
            description="Scraped content for a specific domain",
            mimeType="text/plain",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a specific resource."""
    try:
        if uri == "webscout://history/scraping":
            history = await scraping_service.get_scraping_history()
            return TextContent(
                type="text",
                text=str(history),
            )
        
        elif uri == "webscout://cache/analysis":
            cache = await analysis_service.get_analysis_cache()
            return TextContent(
                type="text",
                text=str(cache),
            )
        
        elif uri.startswith("webscout://") and "/analysis" in uri:
            domain = uri.split("/")[2]
            analysis = await analysis_service.get_cached_analysis(domain)
            if analysis:
                return TextContent(
                    type="text",
                    text=str(analysis),
                )
            else:
                raise ValueError(f"No analysis found for domain: {domain}")
        
        elif uri.startswith("webscout://") and "/content" in uri:
            domain = uri.split("/")[2]
            content = await scraping_service.get_cached_content(domain)
            if content:
                return TextContent(
                    type="text",
                    text=content,
                )
            else:
                raise ValueError(f"No content found for domain: {domain}")
        
        else:
            raise ValueError(f"Unknown resource URI: {uri}")
    
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        raise


@server.list_tools()
async def list_tools() -> List[Tool]:
    """List available tools."""
    return [
        Tool(
            name="scrape_url",
            description="Scrape content from a URL",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to scrape",
                    },
                    "use_javascript": {
                        "type": "boolean",
                        "description": "Whether to use JavaScript rendering (slower but more complete)",
                        "default": False,
                    },
                    "extract_links": {
                        "type": "boolean",
                        "description": "Whether to extract all links from the page",
                        "default": True,
                    },
                    "extract_images": {
                        "type": "boolean",
                        "description": "Whether to extract all images from the page",
                        "default": True,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="search_web",
            description="Search the web for information",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["web", "images", "news", "videos"],
                        "description": "Type of search to perform",
                        "default": "web",
                    },
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="analyze_website",
            description="Perform comprehensive analysis of a website",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to analyze",
                    },
                    "include_seo": {
                        "type": "boolean",
                        "description": "Include SEO analysis",
                        "default": True,
                    },
                    "include_performance": {
                        "type": "boolean",
                        "description": "Include performance analysis",
                        "default": True,
                    },
                    "include_accessibility": {
                        "type": "boolean",
                        "description": "Include accessibility analysis",
                        "default": True,
                    },
                    "include_security": {
                        "type": "boolean",
                        "description": "Include security analysis",
                        "default": True,
                    },
                },
                "required": ["url"],
            },
        ),
        Tool(
            name="analyze_content",
            description="Analyze text content for insights",
            inputSchema={
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The text content to analyze",
                    },
                    "include_sentiment": {
                        "type": "boolean",
                        "description": "Include sentiment analysis",
                        "default": True,
                    },
                    "include_entities": {
                        "type": "boolean",
                        "description": "Include entity extraction",
                        "default": True,
                    },
                    "include_keywords": {
                        "type": "boolean",
                        "description": "Include keyword extraction",
                        "default": True,
                    },
                },
                "required": ["content"],
            },
        ),
        Tool(
            name="search_domain",
            description="Search within a specific domain",
            inputSchema={
                "type": "object",
                "properties": {
                    "domain": {
                        "type": "string",
                        "description": "The domain to search within",
                    },
                    "query": {
                        "type": "string",
                        "description": "The search query",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results to return",
                        "default": 10,
                    },
                },
                "required": ["domain", "query"],
            },
        ),
        Tool(
            name="monitor_website",
            description="Monitor a website for changes",
            inputSchema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to monitor",
                    },
                    "check_interval": {
                        "type": "integer",
                        "description": "Check interval in minutes",
                        "default": 60,
                    },
                    "notify_changes": {
                        "type": "boolean",
                        "description": "Whether to notify about changes",
                        "default": True,
                    },
                },
                "required": ["url"],
            },
        ),
    ]


# Initialize tools handler
web_scout_tools = WebScoutTools(scraping_service, search_service, analysis_service)


@server.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls."""
    try:
        if name == "scrape_url":
            return await web_scout_tools.scrape_url(**arguments)
        elif name == "search_web":
            return await web_scout_tools.search_web(**arguments)
        elif name == "analyze_website":
            return await web_scout_tools.analyze_website(**arguments)
        elif name == "analyze_content":
            return await web_scout_tools.analyze_content(**arguments)
        elif name == "search_domain":
            return await web_scout_tools.search_domain(**arguments)
        elif name == "monitor_website":
            return await web_scout_tools.monitor_website(**arguments)
        else:
            raise ValueError(f"Unknown tool: {name}")
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Main entry point for the MCP server."""
    logger.info(f"Starting {SERVER_NAME} v{SERVER_VERSION}")
    
    # Create cache directory if it doesn't exist
    os.makedirs(config["cache_dir"], exist_ok=True)
    
    # Initialize services
    await scraping_service.initialize()
    await search_service.initialize()
    await analysis_service.initialize()
    
    try:
        # Run the server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream, server.create_initialization_options())
    
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
    
    finally:
        # Cleanup services
        await scraping_service.cleanup()
        await search_service.cleanup()
        await analysis_service.cleanup()


if __name__ == "__main__":
    asyncio.run(main())