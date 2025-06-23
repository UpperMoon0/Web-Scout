"""
Data models for search operations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


class SearchResult:
    """Represents a single search result."""
    
    def __init__(
        self,
        title: str,
        url: str,
        snippet: str,
        source: str = "Unknown",
        thumbnail: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source = source
        self.thumbnail = thumbnail
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source": self.source,
            "thumbnail": self.thumbnail,
            "metadata": self.metadata,
        }


class SearchResponse:
    """Represents a search response with multiple results."""
    
    def __init__(
        self,
        query: str,
        results: List[SearchResult],
        total_results: Optional[int] = None,
        search_type: str = "web",
        timestamp: Optional[str] = None,
    ):
        self.query = query
        self.results = results
        self.total_results = total_results
        self.search_type = search_type
        self.timestamp = timestamp or datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "results": [result.to_dict() for result in self.results],
            "total_results": self.total_results,
            "search_type": self.search_type,
            "timestamp": self.timestamp,
        }