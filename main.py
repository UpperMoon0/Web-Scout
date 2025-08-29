from fastapi import FastAPI
import sys
import os
from .api.routes import router
from .mcp.server import SimpleMCPServer

# Initialize FastAPI app
app = FastAPI()
app.include_router(router)

def main():
    """Main function to run the MCP server or REST API."""
    if len(sys.argv) > 1 and sys.argv[1] == "--mcp":
        # Run as MCP server
        print("Starting Web-Scout MCP server...", file=sys.stderr)
        server = SimpleMCPServer()
        import asyncio
        asyncio.run(server.run())
    else:
        # Run as REST API (existing behavior)
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8000")))

if __name__ == "__main__":
    main()