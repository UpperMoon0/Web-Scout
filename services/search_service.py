from core.config import model
from services.web_scraper import scrape_webpage_content
from utils.prompt_builder import generate_search_prompt
from ddgs import DDGS


async def perform_core_search(query: str, mode_str: str) -> dict:
    """Core search functionality shared between REST API and MCP server."""
    try:
        # Get search results using DDGS
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=10)]

        if not results:
            return {
                "query": query,
                "summary": "No search results found for the query.",
                "sources_used": 0
            }

        # Scrape content from top 5 results
        results_with_content = []
        for i, result in enumerate(results[:5]):
            print(f"Scraping content from: {result.get('href', 'No URL')} ({i+1}/5)")
            content = scrape_webpage_content(result['href'])
            result_with_content = result.copy()
            result_with_content['full_content'] = content
            results_with_content.append(result_with_content)

        # Add remaining results without scraping
        results_with_content.extend(results[5:])

        # Generate prompt and get LLM summary
        prompt = generate_search_prompt(query, results_with_content, mode_str)

        response = model.generate_content(prompt)
        summary = response.text

        return {
            "query": query,
            "mode": mode_str,
            "summary": summary,
            "sources_used": len(results)
        }

    except Exception as e:
        return {
            "query": query,
            "summary": f"Error performing search: {str(e)}",
            "sources_used": 0
        }