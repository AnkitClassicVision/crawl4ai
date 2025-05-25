from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
import os
from typing import Optional

# Import the correct crawler
try:
    from crawl4ai import AsyncWebCrawler
except ImportError:
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
        "version": "1.0.1"
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
        # Use async crawler
        if AsyncWebCrawler:
            async with AsyncWebCrawler(verbose=False) as crawler:
                result = await crawler.arun(
                    url=request.url,
                    wait_for=request.wait_for,
                    css_selector=request.css_selector,
                    screenshot=request.screenshot,
                    js_code=request.js_code
                )
        else:
            # Fallback to sync crawler
            crawler = WebCrawler(verbose=False)
            result = crawler.run(
                url=request.url,
                wait_for=request.wait_for,
                css_selector=request.css_selector,
                screenshot=request.screenshot,
                js_code=request.js_code
            )
        
        # Extract data from result object (not dictionary!)
        response_data = {
            "success": True,
            "url": request.url,
            "markdown": result.markdown if hasattr(result, 'markdown') else "",
            "cleaned_html": result.cleaned_html if hasattr(result, 'cleaned_html') else "",
            "title": result.title if hasattr(result, 'title') else "",
            "links": result.links if hasattr(result, 'links') else {},
            "images": result.images if hasattr(result, 'images') else [],
            "metadata": result.metadata if hasattr(result, 'metadata') else {}
        }
        
        # Add media if it exists
        if hasattr(result, 'media') and result.media:
            response_data["media"] = result.media
        
        return response_data
        
    except Exception as e:
        # Log the error for debugging
        print(f"Crawl error: {str(e)}")
        print(f"Error type: {type(e)}")
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")

# Add a test endpoint
@app.get("/test")
def test_endpoint():
    return {
        "message": "API is running",
        "crawler_available": AsyncWebCrawler is not None
    }
