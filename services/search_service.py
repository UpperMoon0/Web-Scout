import asyncio
import time
import httpx
from services.web_scraper import scrape_webpage_content
from utils.prompt_builder import generate_search_prompt
from services.cache_service import search_cache
from ddgs import DDGS
from core.settings import settings_manager


async def call_llm(prompt: str, model_name: str = None, max_retries: int = 3) -> str:
    """Call LLM via OpenAI-compatible API with retry logic."""
    if model_name is None:
        model_name = settings_manager.get("llm_model", "gemini-3-flash-preview")
    
    llm_endpoint = settings_manager.get("llm_endpoint")
    
    if not llm_endpoint:
        raise Exception("No LLM endpoint configured. Set 'llm_endpoint' in settings.")
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        for attempt in range(max_retries):
            try:
                body = {
                    "model": model_name,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 8192
                }
                
                response = await client.post(f"{llm_endpoint}/v1/chat/completions", json=body)
                
                if response.status_code == 429:
                    wait_time = (2 ** attempt) * 1
                    await asyncio.sleep(wait_time)
                    continue
                    
                response.raise_for_status()
                result = response.json()
                return result["choices"][0]["message"]["content"]
                
            except httpx.HTTPStatusError as e:
                if response.status_code == 401:
                    raise Exception(f"LLM API authentication failed: {e}")
                print(f"LLM API error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
            except Exception as e:
                print(f"Error calling LLM (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(1)
        
        raise Exception("Max retries exceeded for LLM API")


async def perform_core_search(query: str, mode_str: str) -> dict:
    """Core search functionality shared between REST API and MCP server."""
    start_time = time.perf_counter()
    timing = {
        "search_time": 0.0,
        "scrape_time": 0.0,
        "llm_time": 0.0,
        "total_time": 0.0
    }

    try:
        search_start = time.perf_counter()
        loop = asyncio.get_running_loop()
        
        def run_search():
            max_results = settings_manager.get("max_results")
            safe_search = settings_manager.get("safe_search")
            safesearch_param = "on" if safe_search else "off"
            
            with DDGS() as ddgs:
                return [r for r in ddgs.text(query, max_results=max_results, safesearch=safesearch_param)]
        
        results = await loop.run_in_executor(None, run_search)
        timing["search_time"] = time.perf_counter() - search_start

        if not results:
            timing["total_time"] = time.perf_counter() - start_time
            return {
                "query": query,
                "summary": "No search results found for the query.",
                "sources_used": 0,
                "timing": timing
            }

        scrape_start = time.perf_counter()
        tasks = []
        for i, result in enumerate(results[:5]):
            print(f"Scraping content from: {result.get('href', 'No URL')} ({i+1}/5)")
            tasks.append(scrape_webpage_content(result['href']))
        
        scraped_contents = await asyncio.gather(*tasks)
        
        results_with_content = []
        for i, (result, content) in enumerate(zip(results[:5], scraped_contents)):
            result_with_content = result.copy()
            result_with_content['full_content'] = content
            results_with_content.append(result_with_content)
        
        results_with_content.extend(results[5:])
        timing["scrape_time"] = time.perf_counter() - scrape_start

        llm_start = time.perf_counter()
        prompt = generate_search_prompt(query, results_with_content, mode_str)
        
        llm_endpoint = settings_manager.get("llm_endpoint")
        if not llm_endpoint:
            summary_lines = ["**LLM not configured. Displaying top search results:**\n"]
            for i, res in enumerate(results_with_content[:5]):
                title = res.get('title', 'No Title')
                href = res.get('href', '#')
                body = res.get('body', 'No description available.')
                summary_lines.append(f"{i+1}. **[{title}]({href})**\n   {body}\n")
            summary = "\n".join(summary_lines)
        else:
            model_name = settings_manager.get("llm_model", "gemini-3-flash-preview")
            summary = await call_llm(prompt, model_name)
        
        timing["llm_time"] = time.perf_counter() - llm_start
        timing["total_time"] = time.perf_counter() - start_time

        search_cache.add(query, mode_str, results_with_content, summary, timing)

        return {
            "query": query,
            "mode": mode_str,
            "summary": summary,
            "sources_used": len(results),
            "timing": timing
        }

    except Exception as e:
        timing["total_time"] = time.perf_counter() - start_time
        return {
            "query": query,
            "summary": f"Error performing search: {str(e)}",
            "sources_used": 0,
            "timing": timing
        }