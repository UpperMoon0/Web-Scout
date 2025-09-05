import httpx
from bs4 import BeautifulSoup
from typing import Optional
import re
import asyncio


async def scrape_webpage_content(url: str, max_length: int = 3000) -> Optional[str]:
    """Scrape and extract meaningful content from a webpage asynchronously."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        # Fetch webpage asynchronously
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=30.0)
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

    except httpx.RequestError as e:
        print(f"Error scraping {url}: {str(e)}")
        return None
    except Exception as e:
        print(f"Unexpected error scraping {url}: {str(e)}")
        return None