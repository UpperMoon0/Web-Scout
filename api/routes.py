from fastapi import APIRouter, HTTPException, Query
from ..core.config import WEB_SEARCH_TOOL_SCHEMA
from ..services.search_service import perform_core_search
import json

router = APIRouter()

@router.get("/health")
@router.head("/health")
async def health_check():
    return {"status": "ok"}

@router.get("/tools")
async def list_tools():
    """List available MCP tools."""
    return {
        'tools': [WEB_SEARCH_TOOL_SCHEMA]
    }

@router.post("/tools/call")
async def call_tool(request: dict):
    """Execute an MCP tool call."""
    try:
        tool_name = request.get('name')
        arguments = request.get('arguments', {})

        if tool_name == 'web_search':
            query = arguments.get('query', '')
            mode = arguments.get('mode', 'summary')

            if not query:
                raise HTTPException(status_code=400, detail="Query parameter is required")

            result = await perform_core_search(query, mode)

            return {
                'result': {
                    'content': [
                        {
                            'type': 'text',
                            'text': json.dumps(result, indent=2)
                        }
                    ]
                }
            }
        else:
            raise HTTPException(status_code=400, detail=f"Unknown tool: {tool_name}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search(
    query: str,
    mode: int = Query(0, description="Response mode: 0 for summary, 1 for detailed", ge=0, le=1)
):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    if mode not in [0, 1]:
        raise HTTPException(status_code=400, detail="Mode must be 0 (summary) or 1 (detailed)")

    mode_str = "summary" if mode == 0 else "detailed"

    # Use shared core search function
    result = await perform_core_search(query, mode_str)

    # Convert mode string back to integer for REST API response
    result["mode"] = mode
    return result