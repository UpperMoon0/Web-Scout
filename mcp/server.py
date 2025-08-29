import json
import sys
import asyncio
from ..core.config import WEB_SEARCH_TOOL_SCHEMA
from ..services.search_service import perform_core_search


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
                # Use shared schema
                return {
                    'jsonrpc': '2.0',
                    'id': msg_id,
                    'result': {
                        'tools': [WEB_SEARCH_TOOL_SCHEMA]
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

                    # Use shared core search function
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