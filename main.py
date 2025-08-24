from fastapi import FastAPI, HTTPException
from duckduckgo_search import DDGS

app = FastAPI()

@app.get("/health")
@app.head("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/search")
async def search(query: str):
    if not query:
        raise HTTPException(status_code=400, detail="Query parameter is required")
    
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=5)]
        return {"results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))