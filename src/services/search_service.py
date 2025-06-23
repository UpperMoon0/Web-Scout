"""
Search service for the Web Scout MCP Server.

Provides functionality for web searching, domain-specific searches,
and various search types (web, images, news, etc.).
"""

import asyncio
import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib.parse import quote_plus

import aiohttp
import requests

from .search_models import SearchResult, SearchResponse
from .custom_search_engine import CustomSearchEngine

logger = logging.getLogger(__name__)


class SearchService:
    """Service for web search operations."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.user_agent = config.get("user_agent", "Web-Scout-MCP/0.1.0")
        self.timeout = config.get("timeout", 30)
        self.cache_dir = config.get("cache_dir", ".web_scout_cache")
        
        # API keys (if available)
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        self.bing_api_key = os.getenv("BING_API_KEY")
        
        self.search_cache: Dict[str, SearchResponse] = {}
        
        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Initialize custom search engine
        db_path = config.get("custom_search_db", "web_scout_search.db")
        self.custom_search_engine = CustomSearchEngine(db_path, config)
    
    async def initialize(self):
        """Initialize the search service."""
        logger.info("Initializing search service")
        # Load cached searches if exists
        await self._load_cache()
        
        # Initialize custom search engine
        await self.custom_search_engine.initialize()
    
    async def search_web(
        self,
        query: str,
        max_results: int = 10,
        search_type: str = "web",
    ) -> SearchResponse:
        """
        Search the web for information.
        
        Args:
            query: The search query
            max_results: Maximum number of results to return
            search_type: Type of search (web, images, news, videos)
        
        Returns:
            SearchResponse object containing the search results
        """
        logger.info(f"Searching web: '{query}' (type: {search_type})")
        
        cache_key = f"{query}:{search_type}:{max_results}"
        
        # Check cache first
        if cache_key in self.search_cache:
            cached_result = self.search_cache[cache_key]
            logger.info(f"Returning cached search result for: {query}")
            return cached_result
        
        try:
            # Try custom search engine first (Phase 1 implementation)
            response = await self._search_custom(query, max_results, search_type)
            
            # If custom search returns no results, fall back to external APIs
            if not response.results:
                if self.google_api_key and self.google_cse_id:
                    response = await self._search_google(query, max_results, search_type)
                elif self.bing_api_key:
                    response = await self._search_bing(query, max_results, search_type)
                else:
                    # Final fallback to mock search
                    response = await self._search_fallback(query, max_results, search_type)
            
            # Cache the result
            self.search_cache[cache_key] = response
            await self._save_cache()
            
            return response
        
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {e}")
            raise
    
    async def search_domain(
        self,
        domain: str,
        query: str,
        max_results: int = 10,
    ) -> SearchResponse:
        """
        Search within a specific domain.
        
        Args:
            domain: The domain to search within
            query: The search query
            max_results: Maximum number of results to return
        
        Returns:
            SearchResponse object containing the search results
        """
        site_query = f"site:{domain} {query}"
        return await self.search_web(site_query, max_results, "web")
    
    async def search_similar(
        self,
        url: str,
        max_results: int = 10,
    ) -> SearchResponse:
        """
        Search for pages similar to a given URL.
        
        Args:
            url: The URL to find similar pages for
            max_results: Maximum number of results to return
        
        Returns:
            SearchResponse object containing the search results
        """
        related_query = f"related:{url}"
        return await self.search_web(related_query, max_results, "web")
    
    async def _search_custom(
        self, query: str, max_results: int, search_type: str
    ) -> SearchResponse:
        """Search using the custom search engine."""
        logger.info(f"Using custom search engine for query: {query}")
        
        try:
            return await self.custom_search_engine.search(query, max_results, search_type)
        except Exception as e:
            logger.error(f"Custom search failed: {e}")
            # Return empty response instead of raising exception
            return SearchResponse(
                query=query,
                results=[],
                total_results=0,
                search_type=search_type,
            )
    
    async def _search_google(
        self, query: str, max_results: int, search_type: str
    ) -> SearchResponse:
        """Search using Google Custom Search API."""
        base_url = "https://www.googleapis.com/customsearch/v1"
        
        params = {
            "key": self.google_api_key,
            "cx": self.google_cse_id,
            "q": query,
            "num": min(max_results, 10),  # Google CSE max is 10
        }
        
        if search_type == "images":
            params["searchType"] = "image"
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.get(base_url, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Google Search API error: {response.status}")
                
                data = await response.json()
        
        results = []
        for item in data.get("items", []):
            result = SearchResult(
                title=item.get("title", ""),
                url=item.get("link", ""),
                snippet=item.get("snippet", ""),
                source="Google",
                thumbnail=item.get("image", {}).get("thumbnailLink") if search_type == "images" else None,
                metadata=item,
            )
            results.append(result)
        
        total_results = int(data.get("searchInformation", {}).get("totalResults", 0))
        
        return SearchResponse(
            query=query,
            results=results,
            total_results=total_results,
            search_type=search_type,
        )
    
    async def _search_bing(
        self, query: str, max_results: int, search_type: str
    ) -> SearchResponse:
        """Search using Bing Search API."""
        if search_type == "web":
            endpoint = "https://api.bing.microsoft.com/v7.0/search"
        elif search_type == "images":
            endpoint = "https://api.bing.microsoft.com/v7.0/images/search"
        elif search_type == "news":
            endpoint = "https://api.bing.microsoft.com/v7.0/news/search"
        else:
            endpoint = "https://api.bing.microsoft.com/v7.0/search"
        
        headers = {
            "Ocp-Apim-Subscription-Key": self.bing_api_key,
            "User-Agent": self.user_agent,
        }
        
        params = {
            "q": query,
            "count": min(max_results, 50),  # Bing max is 50
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.get(endpoint, headers=headers, params=params) as response:
                if response.status != 200:
                    raise Exception(f"Bing Search API error: {response.status}")
                
                data = await response.json()
        
        results = []
        
        if search_type == "web":
            for item in data.get("webPages", {}).get("value", []):
                result = SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("snippet", ""),
                    source="Bing",
                    metadata=item,
                )
                results.append(result)
        
        elif search_type == "images":
            for item in data.get("value", []):
                result = SearchResult(
                    title=item.get("name", ""),
                    url=item.get("contentUrl", ""),
                    snippet=item.get("encodingFormat", ""),
                    source="Bing Images",
                    thumbnail=item.get("thumbnailUrl"),
                    metadata=item,
                )
                results.append(result)
        
        elif search_type == "news":
            for item in data.get("value", []):
                result = SearchResult(
                    title=item.get("name", ""),
                    url=item.get("url", ""),
                    snippet=item.get("description", ""),
                    source="Bing News",
                    metadata=item,
                )
                results.append(result)
        
        total_results = data.get("totalEstimatedMatches", len(results))
        
        return SearchResponse(
            query=query,
            results=results,
            total_results=total_results,
            search_type=search_type,
        )
    
    async def _search_fallback(
        self, query: str, max_results: int, search_type: str
    ) -> SearchResponse:
        """Fallback search implementation when no API keys are available."""
        logger.warning("No search API keys available, using fallback search")
        
        # Create mock results for demonstration
        results = []
        
        for i in range(min(max_results, 5)):
            result = SearchResult(
                title=f"Search result {i+1} for: {query}",
                url=f"https://example.com/search-result-{i+1}?q={quote_plus(query)}",
                snippet=f"This is a mock search result #{i+1} for the query '{query}'. "
                       f"In a real implementation with API keys, this would show actual search results.",
                source="Mock Search",
                metadata={"mock": True, "result_number": i+1},
            )
            results.append(result)
        
        return SearchResponse(
            query=query,
            results=results,
            total_results=len(results),
            search_type=search_type,
        )
    
    async def _load_cache(self):
        """Load search cache from file."""
        cache_file = os.path.join(self.cache_dir, "search_cache.json")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                
                # Reconstruct SearchResponse objects
                for key, data in cache_data.items():
                    results = [
                        SearchResult(
                            title=r["title"],
                            url=r["url"],
                            snippet=r["snippet"],
                            source=r["source"],
                            thumbnail=r.get("thumbnail"),
                            metadata=r.get("metadata", {}),
                        ) for r in data["results"]
                    ]
                    
                    self.search_cache[key] = SearchResponse(
                        query=data["query"],
                        results=results,
                        total_results=data.get("total_results"),
                        search_type=data["search_type"],
                        timestamp=data["timestamp"],
                    )
            
            except Exception as e:
                logger.warning(f"Failed to load search cache: {e}")
    
    async def _save_cache(self):
        """Save search cache to file."""
        cache_file = os.path.join(self.cache_dir, "search_cache.json")
        try:
            # Keep only recent searches (last 100)
            cache_items = list(self.search_cache.items())[-100:]
            cache_data = {key: response.to_dict() for key, response in cache_items}
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
        
        except Exception as e:
            logger.warning(f"Failed to save search cache: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        await self._save_cache()
        
        # Clean up custom search engine
        await self.custom_search_engine.cleanup()
        
        logger.info("Search service cleaned up")
    
    async def get_search_statistics(self) -> Dict[str, Any]:
        """Get statistics from the custom search engine."""
        return await self.custom_search_engine.get_statistics()