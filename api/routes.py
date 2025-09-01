from fastapi import APIRouter, HTTPException, Query, Request
from core.config import WEB_SEARCH_TOOL_SCHEMA
from services.search_service import perform_core_search
from models.monitoring import MonitoringResponse, ServiceStatus, SystemMetrics
import json
from datetime import datetime

router = APIRouter()


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


@router.post("/mcp")
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
    return {
        "status": "ok",
        "service": "Web-Scout",
        "version": "1.0.0"
    }


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


@router.get("/monitoring")
async def get_monitoring_status() -> MonitoringResponse:
    """
    Get comprehensive monitoring status of the Web Scout service.

    Returns:
        MonitoringResponse: Detailed system status and metrics
    """
    try:
        import psutil
        import time
        from datetime import datetime, timedelta
        
        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        # Calculate uptime
        boot_time = psutil.boot_time()
        uptime = str(timedelta(seconds=time.time() - boot_time))
        
        metrics = SystemMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_info.percent,
            disk_usage=(disk_info.used / disk_info.total) * 100,
            uptime=uptime
        )
        
        # Get service status (search service)
        search_status = ServiceStatus(
            name="Search Service",
            status="healthy",
            details={"ready": True},
            last_updated=datetime.now().isoformat()
        )
        
        # Overall status
        overall_status = "healthy"
        
        return MonitoringResponse(
            status=overall_status,
            service_name="Web-Scout",
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            metrics=metrics,
            services=[search_status]
        )
        
    except ImportError:
        # If psutil is not available, return basic status
        return MonitoringResponse(
            status="healthy",
            service_name="Web-Scout",
            version="1.0.0",
            timestamp=datetime.now().isoformat(),
            details={"message": "Detailed metrics not available (psutil not installed)"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get monitoring status: {str(e)}")


@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Welcome to Web-Scout API 🔍",
        "version": "1.0.0",
        "endpoints": {
            "GET /": "API information",
            "GET /health": "Health check",
            "GET /monitoring": "Comprehensive system monitoring",
            "GET /search": "Perform web search",
            "POST /mcp": "Embedded MCP endpoint"
        },
        "features": [
            "Web search with AI-powered summarization",
            "Multiple response modes (summary/detailed)",
            "MCP (Model Context Protocol) support",
            "Clean API design"
        ],
        "health_endpoint": "/health"
    }