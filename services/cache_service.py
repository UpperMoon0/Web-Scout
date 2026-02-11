from collections import deque
from datetime import datetime
from typing import List, Dict, Any
from core.settings import settings_manager

class SearchCache:
    def __init__(self):
        self.cache = deque()

    def add(self, query: str, mode: str, results: List[Dict[str, Any]], summary: str, timing: Dict[str, float] = None):
        """Add a search result to the cache."""
        cache_entry = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "mode": mode,
            "results": results,
            "summary": summary,
            "timing": timing or {}
        }
        
        self.cache.appendleft(cache_entry)
        
        # Enforce max size dynamically
        max_size = settings_manager.get("max_cache_size")
        while len(self.cache) > max_size:
            self.cache.pop()

    def get_all(self) -> List[Dict[str, Any]]:
        """Return all cached searches."""
        return list(self.cache)

# Global cache instance
search_cache = SearchCache()
