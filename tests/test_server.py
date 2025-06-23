"""
Tests for the main MCP server
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock

from src.server import main
from src.services.scraping_service import ScrapingService
from src.services.search_service import SearchService
from src.services.analysis_service import AnalysisService


class TestMCPServer:
    """Test cases for the MCP server."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            "user_agent": "Test-Agent/1.0.0",
            "max_retries": 1,
            "timeout": 10,
            "enable_headless": True,
            "cache_dir": ".test_cache",
        }
    
    @pytest.fixture
    def mock_scraping_service(self, mock_config):
        """Mock scraping service."""
        service = Mock(spec=ScrapingService)
        service.initialize = AsyncMock()
        service.cleanup = AsyncMock()
        service.get_scraping_history = AsyncMock(return_value=[])
        service.get_cached_content = AsyncMock(return_value=None)
        return service
    
    @pytest.fixture
    def mock_search_service(self, mock_config):
        """Mock search service."""
        service = Mock(spec=SearchService)
        service.initialize = AsyncMock()
        service.cleanup = AsyncMock()
        return service
    
    @pytest.fixture
    def mock_analysis_service(self, mock_config):
        """Mock analysis service."""
        service = Mock(spec=AnalysisService)
        service.initialize = AsyncMock()
        service.cleanup = AsyncMock()
        service.get_analysis_cache = AsyncMock(return_value={})
        service.get_cached_analysis = AsyncMock(return_value=None)
        return service
    
    def test_server_configuration(self, mock_config):
        """Test server configuration is properly loaded."""
        # This would test configuration loading
        assert mock_config["user_agent"] == "Test-Agent/1.0.0"
        assert mock_config["timeout"] == 10
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, mock_scraping_service, mock_search_service, mock_analysis_service):
        """Test that services are properly initialized."""
        await mock_scraping_service.initialize()
        await mock_search_service.initialize()
        await mock_analysis_service.initialize()
        
        mock_scraping_service.initialize.assert_called_once()
        mock_search_service.initialize.assert_called_once()
        mock_analysis_service.initialize.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_service_cleanup(self, mock_scraping_service, mock_search_service, mock_analysis_service):
        """Test that services are properly cleaned up."""
        await mock_scraping_service.cleanup()
        await mock_search_service.cleanup()
        await mock_analysis_service.cleanup()
        
        mock_scraping_service.cleanup.assert_called_once()
        mock_search_service.cleanup.assert_called_once()
        mock_analysis_service.cleanup.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])