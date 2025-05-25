from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import os
from typing import Optional

# Try different import methods for crawl4ai
try:
    from crawl4ai import AsyncWebCrawler
except ImportError:
    try:
        from crawl4ai.web_crawler import AsyncWebCrawler
    except ImportError:
        # Fallback to sync version
        from crawl4ai import WebCrawler
        AsyncWebCrawler = None

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
    return {
        "status": "healthy", 
        "service": "crawl4ai-api",
        "async_available": AsyncWebCrawler is not None
    }

@app.post("/crawl")
async def crawl_endpoint(
    request: CrawlRequest,
    x_api_key: str = Header(None)
):
    # Check API key
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    try:
        # Use sync version if async not available
        if AsyncWebCrawler is None:
            crawler = WebCrawler(verbose=False)
            result = crawler.run(
                url=request.url,
                wait_for=request.wait_for,
                css_selector=request.css_selector,
                screenshot=request.screenshot,
                js_code=request.js_code
            )
        else:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(
                    url=request.url,
                    wait_for=request.wait_for,
                    css_selector=request.css_selector,
                    screenshot=request.screenshot,
                    js_code=request.js_code
                )
        
        # Handle different result structures
        return {
            "success": True,
            "url": request.url,
            "markdown": getattr(result, 'markdown', result.get('markdown', '')),
            "cleaned_html": getattr(result, 'cleaned_html', result.get('cleaned_html', '')),
            "media": getattr(result, 'media', {}),
            "links": getattr(result, 'links', {}),
            "metadata": getattr(result, 'metadata', {})
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")

# Add a simple test endpoi
