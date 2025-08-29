import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash')

# Shared tool schema definition
WEB_SEARCH_TOOL_SCHEMA = {
    'name': 'web_search',
    'description': 'Perform a web search and provide summaries',
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