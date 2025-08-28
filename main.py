from fastapi import FastAPI, HTTPException, Query
from ddgs import DDGS
import os
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Optional

# Load environment variables
load_dotenv()

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
    results_text = "\n".join([
        f"• {result.get('title', 'No title')}\n  {result.get('body', 'No description')}\n  URL: {result.get('href', 'No URL')}"
        for result in search_results[:10]  # Limit to top 10 results
    ])

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

        # Generate prompt and get LLM summary
        prompt = generate_search_prompt(query, results, mode_str)

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