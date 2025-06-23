"""
Web Scout Tools for MCP Server

This module implements the actual tool functionality that gets called
by the MCP server when tools are invoked.
"""

import json
import logging
from typing import Any, Dict, List

from mcp.types import TextContent

logger = logging.getLogger(__name__)


class WebScoutTools:
    """Tool implementations for Web Scout MCP Server."""
    
    def __init__(self, scraping_service, search_service, analysis_service):
        self.scraping_service = scraping_service
        self.search_service = search_service
        self.analysis_service = analysis_service
        self.monitoring_tasks = {}  # For website monitoring
    
    async def scrape_url(
        self,
        url: str,
        use_javascript: bool = False,
        extract_links: bool = True,
        extract_images: bool = True,
    ) -> List[TextContent]:
        """
        Scrape content from a URL.
        
        Args:
            url: The URL to scrape
            use_javascript: Whether to use JavaScript rendering
            extract_links: Whether to extract links
            extract_images: Whether to extract images
        
        Returns:
            List of TextContent objects with the scraped data
        """
        try:
            logger.info(f"Tool: scrape_url called for {url}")
            
            result = await self.scraping_service.scrape_url(
                url=url,
                use_javascript=use_javascript,
                extract_links=extract_links,
                extract_images=extract_images,
            )
            
            # Format the response
            response_data = {
                "url": result.url,
                "title": result.title,
                "content_preview": result.content[:500] + "..." if len(result.content) > 500 else result.content,
                "content_length": len(result.content),
                "link_count": len(result.links),
                "image_count": len(result.images),
                "timestamp": result.timestamp,
                "metadata": result.metadata,
            }
            
            # Include links and images if requested
            if extract_links:
                response_data["links"] = result.links[:20]  # Limit to first 20
            
            if extract_images:
                response_data["images"] = result.images[:20]  # Limit to first 20
            
            return [
                TextContent(
                    type="text",
                    text=f"Successfully scraped {url}\n\n" + json.dumps(response_data, indent=2)
                )
            ]
        
        except Exception as e:
            logger.error(f"Error in scrape_url tool: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error scraping {url}: {str(e)}"
                )
            ]
    
    async def search_web(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "web",
    ) -> List[TextContent]:
        """
        Search the web for information.
        
        Args:
            query: The search query
            max_results: Maximum number of results
            search_type: Type of search (web, images, news, videos)
        
        Returns:
            List of TextContent objects with search results
        """
        try:
            logger.info(f"Tool: search_web called for '{query}' (type: {search_type})")
            
            response = await self.search_service.search_web(
                query=query,
                max_results=max_results,
                search_type=search_type,
            )
            
            # Format the response
            results_data = []
            for result in response.results:
                results_data.append({
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                    "source": result.source,
                })
            
            response_data = {
                "query": response.query,
                "search_type": response.search_type,
                "total_results": response.total_results,
                "returned_results": len(results_data),
                "results": results_data,
                "timestamp": response.timestamp,
            }
            
            return [
                TextContent(
                    type="text",
                    text=f"Search results for '{query}'\n\n" + json.dumps(response_data, indent=2)
                )
            ]
        
        except Exception as e:
            logger.error(f"Error in search_web tool: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error searching for '{query}': {str(e)}"
                )
            ]
    
    async def analyze_website(
        self,
        url: str,
        include_seo: bool = True,
        include_performance: bool = True,
        include_accessibility: bool = True,
        include_security: bool = True,
    ) -> List[TextContent]:
        """
        Perform comprehensive website analysis.
        
        Args:
            url: The URL to analyze
            include_seo: Include SEO analysis
            include_performance: Include performance analysis
            include_accessibility: Include accessibility analysis
            include_security: Include security analysis
        
        Returns:
            List of TextContent objects with analysis results
        """
        try:
            logger.info(f"Tool: analyze_website called for {url}")
            
            # First scrape the website
            scrape_result = await self.scraping_service.scrape_url(url)
            
            # Then analyze it
            analysis = await self.analysis_service.analyze_website(
                url=url,
                html=scrape_result.html,
                content=scrape_result.content,
                metadata=scrape_result.metadata,
                include_seo=include_seo,
                include_performance=include_performance,
                include_accessibility=include_accessibility,
                include_security=include_security,
            )
            
            # Format the response
            analysis_data = analysis.to_dict()
            
            return [
                TextContent(
                    type="text",
                    text=f"Website analysis for {url}\n\n" + json.dumps(analysis_data, indent=2)
                )
            ]
        
        except Exception as e:
            logger.error(f"Error in analyze_website tool: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error analyzing website {url}: {str(e)}"
                )
            ]
    
    async def analyze_content(
        self,
        content: str,
        include_sentiment: bool = True,
        include_entities: bool = True,
        include_keywords: bool = True,
    ) -> List[TextContent]:
        """
        Analyze text content for insights.
        
        Args:
            content: The text content to analyze
            include_sentiment: Include sentiment analysis
            include_entities: Include entity extraction
            include_keywords: Include keyword extraction
        
        Returns:
            List of TextContent objects with analysis results
        """
        try:
            logger.info("Tool: analyze_content called")
            
            analysis = await self.analysis_service.analyze_content(
                content=content,
                include_sentiment=include_sentiment,
                include_entities=include_entities,
                include_keywords=include_keywords,
            )
            
            # Format the response
            analysis_data = analysis.to_dict()
            
            return [
                TextContent(
                    type="text",
                    text="Content analysis results:\n\n" + json.dumps(analysis_data, indent=2)
                )
            ]
        
        except Exception as e:
            logger.error(f"Error in analyze_content tool: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error analyzing content: {str(e)}"
                )
            ]
    
    async def search_domain(
        self,
        domain: str,
        query: str,
        max_results: int = 10,
    ) -> List[TextContent]:
        """
        Search within a specific domain.
        
        Args:
            domain: The domain to search within
            query: The search query
            max_results: Maximum number of results
        
        Returns:
            List of TextContent objects with search results
        """
        try:
            logger.info(f"Tool: search_domain called for domain '{domain}' with query '{query}'")
            
            response = await self.search_service.search_domain(
                domain=domain,
                query=query,
                max_results=max_results,
            )
            
            # Format the response
            results_data = []
            for result in response.results:
                results_data.append({
                    "title": result.title,
                    "url": result.url,
                    "snippet": result.snippet,
                    "source": result.source,
                })
            
            response_data = {
                "domain": domain,
                "query": response.query,
                "total_results": response.total_results,
                "returned_results": len(results_data),
                "results": results_data,
                "timestamp": response.timestamp,
            }
            
            return [
                TextContent(
                    type="text",
                    text=f"Domain search results for '{domain}'\n\n" + json.dumps(response_data, indent=2)
                )
            ]
        
        except Exception as e:
            logger.error(f"Error in search_domain tool: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error searching domain '{domain}': {str(e)}"
                )
            ]
    
    async def monitor_website(
        self,
        url: str,
        check_interval: int = 60,
        notify_changes: bool = True,
    ) -> List[TextContent]:
        """
        Monitor a website for changes.
        
        Args:
            url: The URL to monitor
            check_interval: Check interval in minutes
            notify_changes: Whether to notify about changes
        
        Returns:
            List of TextContent objects with monitoring status
        """
        try:
            logger.info(f"Tool: monitor_website called for {url}")
            
            # This is a simplified implementation
            # In a real implementation, you would set up background tasks
            
            # Take initial snapshot
            initial_result = await self.scraping_service.scrape_url(url)
            
            # Store monitoring info
            self.monitoring_tasks[url] = {
                "url": url,
                "check_interval": check_interval,
                "notify_changes": notify_changes,
                "last_content_hash": hash(initial_result.content),
                "last_check": initial_result.timestamp,
                "changes_detected": 0,
                "status": "active",
            }
            
            response_data = {
                "url": url,
                "status": "monitoring_started",
                "check_interval_minutes": check_interval,
                "initial_content_length": len(initial_result.content),
                "initial_title": initial_result.title,
                "next_check": "In progress...",
                "message": f"Started monitoring {url} with {check_interval} minute intervals",
            }
            
            return [
                TextContent(
                    type="text",
                    text=f"Website monitoring setup for {url}\n\n" + json.dumps(response_data, indent=2)
                )
            ]
        
        except Exception as e:
            logger.error(f"Error in monitor_website tool: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error setting up monitoring for {url}: {str(e)}"
                )
            ]
    
    async def get_monitoring_status(self) -> List[TextContent]:
        """Get status of all monitored websites."""
        try:
            if not self.monitoring_tasks:
                return [
                    TextContent(
                        type="text",
                        text="No websites are currently being monitored."
                    )
                ]
            
            status_data = {
                "active_monitors": len(self.monitoring_tasks),
                "monitors": list(self.monitoring_tasks.values()),
            }
            
            return [
                TextContent(
                    type="text",
                    text="Website monitoring status:\n\n" + json.dumps(status_data, indent=2)
                )
            ]
        
        except Exception as e:
            logger.error(f"Error getting monitoring status: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error getting monitoring status: {str(e)}"
                )
            ]
    
    async def stop_monitoring(self, url: str) -> List[TextContent]:
        """Stop monitoring a specific website."""
        try:
            if url in self.monitoring_tasks:
                del self.monitoring_tasks[url]
                return [
                    TextContent(
                        type="text",
                        text=f"Stopped monitoring {url}"
                    )
                ]
            else:
                return [
                    TextContent(
                        type="text",
                        text=f"No active monitoring found for {url}"
                    )
                ]
        
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            return [
                TextContent(
                    type="text",
                    text=f"Error stopping monitoring for {url}: {str(e)}"
                )
            ]