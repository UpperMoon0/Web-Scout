from dotenv import load_dotenv

load_dotenv()

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