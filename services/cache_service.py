from collections import deque
from datetime import datetime
from typing import List, Dict, Any

class SearchCache:
    def __init__(self, max_size: int = 10):
        self.max_size = max_size
        self.cache = deque(maxlen=max_size)

    def add(self, query: str, mode: str, results: List[Dict[str, Any]], summary: str):
        """Add a search result to the cache."""
        cache_entry = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "mode": mode,
            "results": results,
            "summary": summary
        }
        # If we're at max size, deque handles the removal of the oldest item
        self.cache.appendleft(cache_entry)

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all cached searches."""
        return list(self.cache)

# Global cache instance
search_cache = SearchCache(max_size=10)
