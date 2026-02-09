import sys
import os
sys.path.insert(0, '/app/Web-Scout')

from fastapi import FastAPI
import uvicorn
from api.routes import router
from utils.service_discovery import ServiceDiscovery

# Initialize FastAPI app
app = FastAPI(
    title="Web-Scout",
    description="Web search and AI-powered summarization service with MCP support",
    version="1.0.0"
)
app.include_router(router)

# Service Discovery
sd = None

@app.on_event("startup")
async def startup_event():
    global sd
    port = int(os.getenv("PORT", "8000"))
    sd = ServiceDiscovery(
        service_name="web-scout",
        port=port,
        tags=["mcp", "web-search"]
    )
    sd.start()

@app.on_event("shutdown")
async def shutdown_event():
    if sd:
        sd.deregister()

def main():
    """Start the unified server (REST API + Embedded MCP)."""
    port = int(os.getenv("PORT", "8000"))
    print(f"Starting Web-Scout server on port {port} (HTTP + Embedded MCP)")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port
    )

if __name__ == "__main__":
    main()