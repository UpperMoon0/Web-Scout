import os
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Gemini AI
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

model = None
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-2.5-flash')
else:
    print("WARNING: GEMINI_API_KEY not found. AI features will be disabled.")

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