import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from services.search_service import perform_core_search

# Sample search results
MOCK_SEARCH_RESULTS = [
    {'title': 'Test Result 1', 'href': 'http://test1.com', 'body': 'Snippet 1'},
    {'title': 'Test Result 2', 'href': 'http://test2.com', 'body': 'Snippet 2'},
]

@pytest.mark.asyncio
async def test_search_no_results():
    """Test search when DDGS returns no results."""
    with patch('services.search_service.DDGS') as MockDDGS:
        # Mock DDGS instance and text method
        mock_ddgs_instance = MockDDGS.return_value
        mock_ddgs_instance.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_instance.text.return_value = []

        result = await perform_core_search("query", "summary")
        
        assert result['summary'] == "No search results found for the query."
        assert result['sources_used'] == 0

@pytest.mark.asyncio
async def test_search_with_ai_summary():
    """Test search flow when AI model is available."""
    with patch('services.search_service.DDGS') as MockDDGS, \
         patch('services.search_service.scrape_webpage_content') as mock_scrape, \
         patch('services.search_service.get_llm_model_with_retry') as mock_get_model:
        
        # Mock DDGS
        mock_ddgs_instance = MockDDGS.return_value
        mock_ddgs_instance.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_instance.text.return_value = MOCK_SEARCH_RESULTS
        
        # Mock Scraper
        mock_scrape.return_value = "Full scraped content"
        
        # Mock AI Model
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "AI Generated Summary"
        mock_model.generate_content.return_value = mock_response
        mock_model.generate_content_async = AsyncMock(return_value=mock_response)
        
        # Mock get_llm_model_with_retry to return our mock model
        mock_get_model.return_value = mock_model

        result = await perform_core_search("query", "summary")
        
        assert result['summary'] == "AI Generated Summary"
        assert result['sources_used'] == 2
        mock_model.generate_content_async.assert_called_once()

@pytest.mark.asyncio
async def test_search_without_ai_key_fallback():
    """Test fallback formatting when AI model is None."""
    with patch('services.search_service.DDGS') as MockDDGS, \
         patch('services.search_service.scrape_webpage_content') as mock_scrape, \
         patch('services.search_service.get_llm_model_with_retry', return_value=None): # Mock model as None
        
        # Mock DDGS
        mock_ddgs_instance = MockDDGS.return_value
        mock_ddgs_instance.__enter__.return_value = mock_ddgs_instance
        mock_ddgs_instance.text.return_value = MOCK_SEARCH_RESULTS
        
        # Mock Scraper
        mock_scrape.return_value = "Full scraped content"

        result = await perform_core_search("query", "summary")
        
        # Check that we got the fallback formatted list
        assert "AI Summarization unavailable" in result['summary']
        assert "Test Result 1" in result['summary']
        assert "http://test1.com" in result['summary']
        assert result['sources_used'] == 2
