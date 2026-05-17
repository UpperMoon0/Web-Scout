import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.search_service import perform_core_search

MOCK_SEARCH_RESULTS = [
    {'title': 'Test Result 1', 'href': 'http://test1.com', 'body': 'Snippet 1'},
    {'title': 'Test Result 2', 'href': 'http://test2.com', 'body': 'Snippet 2'},
]


@pytest.mark.asyncio
async def test_search_no_results():
    """Test search when DDGS returns no results."""
    with patch('services.search_service.DDGS') as MockDDGS:
        mock_ddgs_instance = MockDDGS.return_value
        mock_ddgs_instance.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_instance.text.return_value = []

        result = await perform_core_search("query", "summary")
        
        assert result['summary'] == "No search results found for the query."
        assert result['sources_used'] == 0


@pytest.mark.asyncio
async def test_search_with_llm():
    """Test search flow when LLM endpoint is configured."""
    with patch('services.search_service.DDGS') as MockDDGS, \
         patch('services.search_service.scrape_webpage_content') as mock_scrape, \
         patch('services.search_service.settings_manager') as mock_settings, \
         patch('services.search_service.call_llm') as mock_call_llm:
        
        mock_ddgs_instance = MockDDGS.return_value
        mock_ddgs_instance.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_instance.text.return_value = MOCK_SEARCH_RESULTS
        
        mock_scrape.return_value = "Full scraped content"
        
        mock_settings.get.side_effect = lambda key: {
            "llm_endpoint": "http://localhost:11435",
            "llm_model": "gemini-3-flash-preview",
            "max_results": 10,
            "safe_search": True,
        }.get(key)
        
        mock_call_llm.return_value = "AI Generated Summary"

        result = await perform_core_search("query", "summary")
        
        assert result['summary'] == "AI Generated Summary"
        assert result['sources_used'] == 2
        mock_call_llm.assert_called_once()


@pytest.mark.asyncio
async def test_search_without_llm_endpoint_fallback():
    """Test fallback formatting when LLM endpoint is not configured."""
    with patch('services.search_service.DDGS') as MockDDGS, \
         patch('services.search_service.scrape_webpage_content') as mock_scrape, \
         patch('services.search_service.settings_manager') as mock_settings:
        
        mock_ddgs_instance = MockDDGS.return_value
        mock_ddgs_instance.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_instance.text.return_value = MOCK_SEARCH_RESULTS
        
        mock_scrape.return_value = "Full scraped content"
        
        mock_settings.get.side_effect = lambda key: {
            "llm_endpoint": "",
            "llm_model": "gemini-3-flash-preview",
            "max_results": 10,
            "safe_search": True,
        }.get(key)

        result = await perform_core_search("query", "summary")
        
        assert "LLM not configured" in result['summary']
        assert "Test Result 1" in result['summary']
        assert "http://test1.com" in result['summary']
        assert result['sources_used'] == 2