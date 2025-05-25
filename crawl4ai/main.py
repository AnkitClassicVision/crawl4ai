from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from crawl4ai import AsyncWebCrawler
import os
from typing import Optional

app = FastAPI()

# Get API key from environment
API_KEY = os.getenv("API_KEY", "mybcat-secret-key-2024")

class CrawlRequest(BaseModel):
    url: str
    wait_for: Optional[str] = None
    css_selector: Optional[str] = None
    screenshot: bool = False
    js_code: Optional[str] = None

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "crawl4ai-api"}

@app.post("/crawl")
async def crawl_endpoint(
    request: CrawlRequest,
    x_api_key: str = Header(None)
):
    # Check API key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        async with AsyncWebCrawler(verbose=False) as crawler:
            result = await crawler.arun(
                url=request.url,
                wait_for=request.wait_for,
                css_selector=request.css_selector,
                screenshot=request.screenshot,
                js_code=request.js_code
            )
            
            return {
                "success": True,
                "url": request.url,
                "markdown": result.markdown,
                "cleaned_html": result.cleaned_html,
                "media": {
                    "images": result.media.get("images", []),
                    "videos": result.media.get("videos", [])
                },
                "links": {
                    "internal": result.links.get("internal", []),
                    "external": result.links.get("external", [])
                },
                "metadata": result.metadata
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")
