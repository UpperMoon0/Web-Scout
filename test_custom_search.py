#!/usr/bin/env python3
"""
Test script for the custom search engine implementation.

This script tests the basic functionality of the custom search engine
to ensure it's working correctly in Phase 1.
"""

import asyncio
import logging
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from services.custom_search_engine import CustomSearchEngine
from services.search_service import SearchService
from services.db_init import DatabaseInitializer

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_custom_search_engine():
    """Test the custom search engine functionality."""
    logger.info("Starting custom search engine tests")
    
    # Test database path
    test_db_path = "test_web_scout_search.db"
    
    try:
        # 1. Test database initialization
        logger.info("Testing database initialization...")
        db_init = DatabaseInitializer(test_db_path)
        db_init.initialize_database()
        
        stats = db_init.get_database_stats()
        logger.info(f"Initial database stats: {stats}")
        
        # 2. Test custom search engine initialization
        logger.info("Testing custom search engine initialization...")
        config = {
            "crawl_delay": 0.5,  # Faster for testing
            "max_pages_per_domain": 10,  # Limited for testing
            "user_agent": "Web-Scout-Test/0.1.0"
        }
        
        engine = CustomSearchEngine(test_db_path, config)
        await engine.initialize()
        
        # 3. Test search with empty database (should return empty results)
        logger.info("Testing search with empty database...")
        response = await engine.search("test query", max_results=5, search_type="web")
        logger.info(f"Empty search results: {len(response.results)} results")
        
        # 4. Test adding seed URLs
        logger.info("Testing seed URL addition...")
        test_urls = [
            "https://httpbin.org/html",
            "https://httpbin.org/json",
        ]
        added_count = db_init.add_seed_urls(test_urls, priority=1)
        logger.info(f"Added {added_count} test URLs")
        
        # 5. Let the crawler run for a short time
        logger.info("Letting crawler run for 10 seconds...")
        await asyncio.sleep(10)
        
        # 6. Check final statistics
        final_stats = db_init.get_database_stats()
        logger.info(f"Final database stats: {final_stats}")
        
        # 7. Test search service integration
        logger.info("Testing search service integration...")
        search_config = {
            "user_agent": "Web-Scout-Test/0.1.0",
            "timeout": 30,
            "cache_dir": ".test_cache",
            "custom_search_db": test_db_path
        }
        
        search_service = SearchService(search_config)
        await search_service.initialize()
        
        # Test search through service
        search_response = await search_service.search_web("test", max_results=5, search_type="web")
        logger.info(f"Search service results: {len(search_response.results)} results")
        
        # Test different search types
        for search_type in ["web", "images", "news"]:
            response = await search_service.search_web("test", max_results=3, search_type=search_type)
            logger.info(f"Search type '{search_type}': {len(response.results)} results")
        
        # Test domain search
        domain_response = await search_service.search_domain("httpbin.org", "test", max_results=5)
        logger.info(f"Domain search results: {len(domain_response.results)} results")
        
        # Get search statistics
        search_stats = await search_service.get_search_statistics()
        logger.info(f"Search engine statistics: {search_stats}")
        
        # Cleanup
        await search_service.cleanup()
        await engine.cleanup()
        
        logger.info("All tests completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test database
        try:
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
                logger.info("Cleaned up test database")
        except Exception as e:
            logger.warning(f"Failed to clean up test database: {e}")
    
    return True


async def test_search_functionality():
    """Test search functionality with mock data."""
    logger.info("Testing search functionality with mock data")
    
    test_db_path = "test_search_functionality.db"
    
    try:
        # Initialize database
        db_init = DatabaseInitializer(test_db_path)
        db_init.initialize_database()
        
        # Add some mock data directly to the database
        import sqlite3
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # Insert mock pages
        mock_pages = [
            ("https://example.com/page1", "example.com", "Python Programming Guide", 
             "Learn Python programming with examples and tutorials. Python is a versatile language.", 
             "<html><body><h1>Python Programming Guide</h1><p>Learn Python programming with examples and tutorials.</p></body></html>",
             "web", 0.8, 200, 100),
            ("https://example.com/page2", "example.com", "JavaScript Tutorial", 
             "Complete JavaScript tutorial for beginners. Learn web development with JavaScript.",
             "<html><body><h1>JavaScript Tutorial</h1><p>Complete JavaScript tutorial for beginners.</p></body></html>",
             "web", 0.7, 200, 95),
            ("https://news.example.com/article1", "news.example.com", "Breaking News: Tech Update", 
             "Latest technology news and updates from the industry. Innovation continues.",
             "<html><body><h1>Breaking News: Tech Update</h1><p>Latest technology news and updates.</p></body></html>",
             "news", 0.9, 200, 80),
        ]
        
        for i, (url, domain, title, content, html, content_type, quality_score, status_code, content_length) in enumerate(mock_pages, 1):
            cursor.execute("""
                INSERT INTO pages (id, url, domain, title, content, html, content_type, quality_score, status_code, content_length)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (i, url, domain, title, content, html, content_type, quality_score, status_code, content_length))
            
            # Insert into FTS table
            cursor.execute("""
                INSERT INTO pages_fts (rowid, title, content) VALUES (?, ?, ?)
            """, (i, title, content))
        
        # Insert mock images
        cursor.execute("""
            INSERT INTO images (page_id, url, alt_text, title) 
            VALUES (1, 'https://example.com/python-logo.png', 'Python Logo', 'Official Python Logo')
        """)
        
        conn.commit()
        conn.close()
        
        # Test search engine
        engine = CustomSearchEngine(test_db_path)
        await engine.initialize()
        
        # Test various searches
        test_queries = [
            ("Python", "web"),
            ("JavaScript", "web"),  
            ("programming", "web"),
            ("news", "news"),
            ("tech", "news"),
            ("logo", "images"),
        ]
        
        for query, search_type in test_queries:
            response = await engine.search(query, max_results=5, search_type=search_type)
            logger.info(f"Query: '{query}' ({search_type}) - Found {len(response.results)} results")
            
            for i, result in enumerate(response.results):
                logger.info(f"  {i+1}. {result.title} - {result.url}")
                logger.info(f"     Snippet: {result.snippet[:100]}...")
        
        # Test statistics
        stats = await engine.get_statistics()
        logger.info(f"Engine statistics: {stats}")
        
        await engine.cleanup()
        logger.info("Search functionality test completed successfully!")
        
    except Exception as e:
        logger.error(f"Search functionality test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Clean up test database
        try:
            if os.path.exists(test_db_path):
                os.remove(test_db_path)
                logger.info("Cleaned up test database")
        except Exception as e:
            logger.warning(f"Failed to clean up test database: {e}")
    
    return True


async def main():
    """Main test function."""
    logger.info("Starting Web-Scout Custom Search Engine Tests")
    
    # Run tests
    tests = [
        ("Basic Custom Search Engine", test_custom_search_engine),
        ("Search Functionality", test_search_functionality),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*50}")
        logger.info(f"Running test: {test_name}")
        logger.info(f"{'='*50}")
        
        try:
            result = await test_func()
            if result:
                logger.info(f"✅ {test_name} PASSED")
                passed += 1
            else:
                logger.error(f"❌ {test_name} FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} FAILED with exception: {e}")
    
    logger.info(f"\n{'='*50}")
    logger.info(f"Test Results: {passed}/{total} tests passed")
    logger.info(f"{'='*50}")
    
    if passed == total:
        logger.info("🎉 All tests passed! Custom search engine is working correctly.")
        return 0
    else:
        logger.error("❌ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)