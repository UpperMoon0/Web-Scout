from core.config import model
from services.web_scraper import scrape_webpage_content
from utils.prompt_builder import generate_search_prompt
from ddgs import DDGS
import asyncio
from concurrent.futures import ThreadPoolExecutor


async def perform_core_search(query: str, mode_str: str) -> dict:
    """Core search functionality shared between REST API and MCP server."""
    try:
        # Run DDGS search in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            def sync_search():
                with DDGS() as ddgs:
                    return [r for r in ddgs.text(query, max_results=10)]
            results = await loop.run_in_executor(executor, sync_search)

        if not results:
            return {
                "query": query,
                "summary": "No search results found for the query.",
                "sources_used": 0
            }

        # Scrape content from top 5 results asynchronously
        scrape_tasks = []
        for i, result in enumerate(results[:5]):
            print(f"Scraping content from: {result.get('href', 'No URL')} ({i+1}/5)")
            scrape_tasks.append(scrape_webpage_content(result['href']))
        
        # Wait for all scraping tasks to complete, allowing exceptions
        contents = await asyncio.gather(*scrape_tasks, return_exceptions=True)

        results_with_content = []
        successful_scrapes = 0
        for i, (result, content) in enumerate(zip(results[:5], contents)):
            if isinstance(content, Exception):
                print(f"Failed to scrape {result.get('href', 'No URL')}: {content}")
                result_with_content = result.copy()
                result_with_content['full_content'] = None
            else:
                result_with_content = result.copy()
                result_with_content['full_content'] = content
                successful_scrapes += 1
            results_with_content.append(result_with_content)

        # Add remaining results without scraping
        results_with_content.extend(results[5:])

        # Generate prompt and get LLM summary (run in thread pool if synchronous)
        prompt = generate_search_prompt(query, results_with_content, mode_str)
        
        # Run model generation in thread pool to avoid blocking - create new executor
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            def sync_generate():
                response = model.generate_content(prompt)
                return response.text
            
            summary = await loop.run_in_executor(executor, sync_generate)

        return {
            "query": query,
            "mode": mode_str,
            "summary": summary,
            "sources_used": len(results),
            "successful_scrapes": successful_scrapes,
            "total_scrapes_attempted": min(5, len(results))
        }

    except Exception as e:
        # Ensure we always return a valid dict even on complete failure
        return {
            "query": query,
            "summary": f"Error performing search: {str(e)}",
            "sources_used": 0,
            "successful_scrapes": 0,
            "total_scrapes_attempted": 0
        }