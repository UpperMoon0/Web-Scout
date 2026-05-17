from fastapi import APIRouter, HTTPException, Query, Request
from core.config import WEB_SEARCH_TOOL_SCHEMA
from services.search_service import perform_core_search
from services.cache_service import search_cache
from core.settings import settings_manager
import json

router = APIRouter()
mcp_router = APIRouter()



import copy

async def handle_json_rpc_message(message: dict) -> dict:
    """Handle a single JSON-RPC message for embedded MCP."""
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
            # Create a deep copy of the schema to modify defaults dynamically
            schema = copy.deepcopy(WEB_SEARCH_TOOL_SCHEMA)
            default_mode = settings_manager.get("search_mode")
            if 'inputSchema' in schema and 'properties' in schema['inputSchema'] and 'mode' in schema['inputSchema']['properties']:
                schema['inputSchema']['properties']['mode']['default'] = default_mode

            return {
                'jsonrpc': '2.0',
                'id': msg_id,
                'result': {
                    'tools': [schema]
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

                result = await perform_core_search(query, mode)
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


@mcp_router.post("/mcp")
async def embedded_mcp_endpoint(request: Request):
    """Embedded MCP endpoint that handles JSON-RPC messages over HTTP."""
    try:
        json_data = await request.json()

        # Check if this is a JSON-RPC message
        if 'jsonrpc' in json_data and 'method' in json_data:
            response = await handle_json_rpc_message(json_data)
            return response
        else:
            raise HTTPException(status_code=400, detail="Not a valid JSON-RPC message")

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
@router.head("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/cache")
async def get_cache():
    """Retrieve cached search results."""
    return search_cache.get_all()


@router.get("/search")
async def search(
    query: str,
    mode: str = Query("summary", description="Response mode: 'summary' or 'detailed'")
):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")

    if mode not in ["summary", "detailed"]:
        raise HTTPException(status_code=400, detail="Mode must be 'summary' or 'detailed'")

    # Use shared core search function
    result = await perform_core_search(query, mode)

    return result


@router.get("/settings")
async def get_settings():
    """Retrieve current configuration settings."""
    return settings_manager.get_settings()


@router.post("/settings")
async def update_settings(settings: dict):
    """Update configuration settings."""
    return settings_manager.save_settings(settings)
