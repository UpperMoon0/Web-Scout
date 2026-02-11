import asyncio
import os
import time
import google.generativeai as genai
from google.api_core.exceptions import TooManyRequests, ServiceUnavailable
from services.web_scraper import scrape_webpage_content
from utils.prompt_builder import generate_search_prompt
from services.cache_service import search_cache
from ddgs import DDGS
from core.settings import settings_manager


def get_llm_model_with_retry(api_key: str = None, model_name: str = None):
    """Get configured Gemini model."""
    if not api_key:
        api_key = os.getenv("GEMINI_API_KEY")
    
    if not model_name:
        model_name = settings_manager.get("gemini_model")

    if not api_key:
        return None

    try:
        genai.configure(api_key=api_key)
        return genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"Error configuring Gemini: {e}")
        return None


async def call_gemini_with_retry(model, prompt: str, max_retries: int = 3) -> str:
    """Call Gemini API with round-robin retry on rate limit."""
    api_keys = settings_manager.get_raw_api_keys()
    key_count = len(api_keys)
    
    for attempt in range(max_retries):
        try:
            # Use async generation if available
            if hasattr(model, 'generate_content_async'):
                response = await model.generate_content_async(prompt)
            else:
                # Fallback for models without async support
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(None, model.generate_content, prompt)
            return response.text
        except (TooManyRequests, ServiceUnavailable) as e:
            print(f"Rate limit error (attempt {attempt + 1}/{max_retries}): {e}")
            # Advance to next key for round-robin
            if key_count > 1:
                settings_manager.advance_api_key()
                # Get next key and reconfigure
                current_index = settings_manager.get_current_api_key_index()
                next_key = api_keys[current_index]
                model = get_llm_model_with_retry(api_key=next_key)
                if model is None:
                    raise Exception("No valid API key available after retry")
            else:
                # Single key, wait and retry with exponential backoff
                wait_time = (2 ** attempt) * 1
                await asyncio.sleep(wait_time)
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            raise
    
    raise Exception("Max retries exceeded for Gemini API")


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
        # Get search results using DDGS in a separate thread to avoid blocking
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

        # Concurrently scrape content from top 5 results
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
        
        # Add remaining results without scraping
        results_with_content.extend(results[5:])
        timing["scrape_time"] = time.perf_counter() - scrape_start

        # Generate prompt and get LLM summary asynchronously
        llm_start = time.perf_counter()
        prompt = generate_search_prompt(query, results_with_content, mode_str)
        
        # Get API key for round-robin
        api_keys = settings_manager.get_raw_api_keys()
        if api_keys:
            current_index = settings_manager.get_current_api_key_index()
            api_key = api_keys[current_index]
        else:
            api_key = os.getenv("GEMINI_API_KEY")
        
        model = get_llm_model_with_retry(api_key=api_key)

        if model:
            summary = await call_gemini_with_retry(model, prompt)
        else:
            # Fallback: Generate a basic summary from search snippets
            summary_lines = ["**AI Summarization unavailable. Displaying top search results:**\n"]
            for i, res in enumerate(results_with_content[:5]):
                title = res.get('title', 'No Title')
                href = res.get('href', '#')
                body = res.get('body', 'No description available.')
                summary_lines.append(f"{i+1}. **[{title}]({href})**\n   {body}\n")
            
            summary = "\n".join(summary_lines)
        timing["llm_time"] = time.perf_counter() - llm_start

        timing["total_time"] = time.perf_counter() - start_time

        # Advance to next key for round-robin after successful call
        if api_keys:
            settings_manager.advance_api_key()

        # Add to cache
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
