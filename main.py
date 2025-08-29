import sys
import os
sys.path.insert(0, '/app/Web-Scout')

from fastapi import FastAPI
import uvicorn
from api.routes import router

# Initialize FastAPI app
app = FastAPI(
    title="Web-Scout",
    description="Web search and AI-powered summarization service with MCP support",
    version="1.0.0"
)
app.include_router(router)

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