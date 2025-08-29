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