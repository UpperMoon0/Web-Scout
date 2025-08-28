from fastapi import FastAPI, HTTPException, Query
from ddgs import DDGS
import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional
import requests
from bs4 import BeautifulSoup
import time
import re
import sys
import json
import asyncio

# Load environment variables
load_dotenv()

def scrape_webpage_content(url: str, max_length: int = 3000) -> Optional[str]:
    """Scrape and extract meaningful content from a webpage."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Fetch webpage
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parse HTML
        soup = BeautifulSoup(response.content, 'lxml')

        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'sidebar']):
            element.decompose()

        # Extract main content using common selectors
        content_elements = []

        # Try to find main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content') or soup.find('div', class_='post-content')

        if main_content:
            # Get text from main content area
            paragraphs = main_content.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            content_elements.extend(paragraphs)

        # If no main content found, extract from body
        paragraphs = soup.find_all('p')
        content_elements.extend(paragraphs)

        # Extract and clean text
        content_text = []
        for element in content_elements[:50]:  # Limit to first 50 relevant elements
            text = element.get_text().strip()
            if text and len(text) > 50:  # Filter out very short texts
                # Clean up whitespace
                text = re.sub(r'\s+', ' ', text)
                content_text.append(text)

        # Join and limit content length
        full_content = ' '.join(content_text)
        if len(full_content) > max_length:
            full_content = full_content[:max_length] + '...'

        return full_content.strip() if full_content else None

    except requests.RequestException as e:
        print(f"Error scraping {url}: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error scraping {url}: {str(e)}")
        return None

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

app = FastAPI()

@app.get("/health")
@app.head("/health")
async def health_check():
    return {"status": "ok"}

def generate_search_prompt(query: str, search_results: list, mode: str) -> str:
    """Generate a prompt for the LLM based on search results and mode."""
    results_text = ""

    for result in search_results[:10]:  # Limit to top 10 results
        title = result.get('title', 'No title')
        body = result.get('body', 'No description')
        href = result.get('href', 'No URL')
        content = result.get('full_content')

        results_text += f"• {title}\n  URL: {href}\n"

        if content:
            # Include scraped content (truncate if too long)
            content_preview = content[:1000] + "..." if len(content) > 1000 else content
            results_text += f"  Content: {content_preview}\n"
        else:
            # Fall back to search snippet
            results_text += f"  Snippet: {body}\n"

        results_text += "\n"

    if mode == "summary":
        prompt = f"""Based on the following search results for the query: "{query}"

Please provide a concise summary of the key findings in 2-3 paragraphs. Focus on the most relevant and important information.

Search Results:
{results_text}

Summary:"""
    elif mode == "detailed":
        prompt = f"""Based on the following search results for the query: "{query}"

Please provide a detailed analysis in 4-5 paragraphs, covering:
1. Main themes and topics found
2. Key insights and important details
3. Different perspectives if available
4. Any notable trends or patterns

Cite specific sources when relevant.

Search Results:
{results_text}

Detailed Analysis:"""
    else:
        raise ValueError("Mode must be 'summary' or 'detailed'")

    return prompt

@app.get("/search")
async def search(
    query: str,
    mode: int = Query(0, description="Response mode: 0 for summary, 1 for detailed", ge=0, le=1)
):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    if mode not in [0, 1]:
        raise HTTPException(status_code=400, detail="Mode must be 0 (summary) or 1 (detailed)")

    mode_str = "summary" if mode == 0 else "detailed"
    try:
        # Get search results
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=10)]

        if not results:
            raise HTTPException(status_code=404, detail="No search results found")

        # Scrape content from top 5 results to avoid overloading
        results_with_content = []
        for i, result in enumerate(results[:5]):  # Only scrape first 5 to keep response time reasonable
            print(f"Scraping content from: {result.get('href', 'No URL')} ({i+1}/5)")
            content = scrape_webpage_content(result['href'])
            result_with_content = result.copy()
            result_with_content['full_content'] = content
            results_with_content.append(result_with_content)

        # Add remaining results without scraping (if any)
        results_with_content.extend(results[5:])

        # Generate prompt and get LLM summary
        prompt = generate_search_prompt(query, results_with_content, mode_str)

        response = model.generate_content(prompt)
        summary = response.text

        return {
            "query": query,
            "mode": mode,
            "summary": summary,
            "sources_used": len(results)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# MCP Server Implementation (Simple JSON-RPC)
async def perform_web_search(query: str, mode: str = "summary") -> dict:
    """Perform web search using the existing logic."""
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
            print(f"MCP Server: Scraping content from: {result.get('href', 'No URL')} ({i+1}/5)")
            content = scrape_webpage_content(result['href'])
            result_with_content = result.copy()
            result_with_content['full_content'] = content
            results_with_content.append(result_with_content)

        # Add remaining results without scraping
        results_with_content.extend(results[5:])

        # Generate prompt and get LLM summary
        prompt = generate_search_prompt(query, results_with_content, mode)

        response = model.generate_content(prompt)
        summary = response.text

        return {
            "query": query,
            "mode": mode,
            "summary": summary,
            "sources_used": len(results)
        }

    except Exception as e:
        return {
            "query": query,
            "summary": f"Error performing search: {str(e)}",
            "sources_used": 0
        }


# Simple MCP Server using JSON-RPC over stdio
class SimpleMCPServer:
    def __init__(self):
        self.request_id = 0

    async def handle_message(self, message: dict) -> dict:
        """Handle incoming MCP messages."""
        try:
            method = message.get('method')
            params = message.get('params', {})
            msg_id = message.get('id')

            if method == 'initialize':
                return {
                    'jsonrpc': '2.0',
                    'id': msg_id,
                    'result': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {
                            'tools': {}
                        },
                        'serverInfo': {
                            'name': 'web-scout-mcp',
                            'version': '1.0.0'
                        }
                    }
                }

            elif method == 'tools/list':
                return {
                    'jsonrpc': '2.0',
                    'id': msg_id,
                    'result': {
                        'tools': [
                            {
                                'name': 'web_search',
                                'description': 'Perform a web search using DuckDuckGo and generate AI-powered summaries',
                                'inputSchema': {
                                    'type': 'object',
                                    'properties': {
                                        'query': {
                                            'type': 'string',
                                            'description': 'The search query to perform'
                                        },
                                        'mode': {
                                            'type': 'string',
                                            'description': 'Response mode: "summary" for concise summary, "detailed" for in-depth analysis',
                                            'enum': ['summary', 'detailed'],
                                            'default': 'summary'
                                        }
                                    },
                                    'required': ['query']
                                }
                            }
                        ]
                    }
                }

            elif method == 'tools/call':
                tool_name = params.get('name')
                tool_args = params.get('arguments', {})

                if tool_name == 'web_search':
                    query = tool_args.get('query', '')
                    mode = tool_args.get('mode', 'summary')

                    if not query:
                        raise ValueError("Query parameter is required")

                    result = await perform_web_search(query, mode)
                    result_json = json.dumps(result, indent=2)

                    return {
                        'jsonrpc': '2.0',
                        'id': msg_id,
                        'result': {
                            'content': [
                                {
                                    'type': 'text',
                                    'text': result_json
                                }
                            ]
                        }
                    }
                else:
                    raise ValueError(f"Unknown tool: {tool_name}")

            else:
                return {
                    'jsonrpc': '2.0',
                    'id': msg_id,
                    'error': {
                        'code': -32601,
                        'message': f'Method not found: {method}'
                    }
                }

        except Exception as e:
            return {
                'jsonrpc': '2.0',
                'id': message.get('id'),
                'error': {
                    'code': -32603,
                    'message': str(e)
                }
            }

    async def run(self):
        """Run the MCP server."""
        try:
            while True:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                if not line:
                    break

                line = line.strip()
                if not line:
                    continue

                try:
                    message = json.loads(line)
                    response = await self.handle_message(message)

                    if response:
                        response_str = json.dumps(response)
                        print(response_str, flush=True)

                except json.JSONDecodeError as e:
                    error_response = {
                        'jsonrpc': '2.0',
                        'id': None,
                        'error': {
                            'code': -32700,
                            'message': f'Parse error: {str(e)}'
                        }
                    }
                    print(json.dumps(error_response), flush=True)

        except KeyboardInterrupt:
            pass


def main():
    """Main function to run the MCP server or REST API."""
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp":
        # Run as MCP server
        print("Starting Web-Scout MCP server...", file=sys.stderr)
        server = SimpleMCPServer()
        asyncio.run(server.run())
    else:
        # Run as REST API (existing behavior)
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))


if __name__ == "__main__":
    main()