import os
from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse

from app.models.schemas import SearchResponse, ScrapeUrlResponse
from app.api.endpoints import (
    search_news_endpoint, 
    scrape_url_endpoint, 
    get_available_sources, 
    get_available_categories,
    search_by_source_category
)
from config.settings import settings


# Initialize FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint - API health check."""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "status": "operational",
        "version": settings.APP_VERSION,
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.APP_VERSION
    }


# News Search Endpoints
@app.get("/api/v1/search", response_model=SearchResponse, tags=["News Search"])
async def search_news_api(
    query: str,
    sources: str = None,
    category: str = None,
    format: str = "json",
    api_key: str = None
):
    """Search for news articles across multiple sources."""
    return await search_news_endpoint(query, sources, category, format, api_key)


# URL Scraping Endpoints  
@app.post("/api/v1/scrape-url", response_model=ScrapeUrlResponse, tags=["URL Scraping"])
async def scrape_url_api(request: dict, api_key: str = None):
    """Scrape content from a specific URL and return it in markdown format."""
    from app.models.schemas import ScrapeUrlRequest
    scrape_request = ScrapeUrlRequest(**request)
    return await scrape_url_endpoint(scrape_request, api_key)


# Configuration Endpoints
@app.get("/api/v1/sources", tags=["Configuration"])
async def get_sources_api(api_key: str = None):
    """Get list of available news sources."""
    return await get_available_sources(api_key)


@app.get("/api/v1/categories", tags=["Configuration"])
async def get_categories_api(api_key: str = None):
    """Get list of available news categories."""
    return await get_available_categories(api_key)


@app.get("/api/v1/search/by-category", response_model=SearchResponse, tags=["News Search"])
async def search_by_source_category_api(
    query: str,
    source_category: str,
    category: str = None,
    format: str = "json",
    api_key: str = None
):
    """
    Search for news articles by source category.
    
    Available source categories:
    - search_engine: Google Search, DuckDuckGo
    - news_aggregator: Google News, Bing News  
    - international_news: BBC News, CNN
    - national_news: Detik, Kompas (Indonesian)
    - blog_platform: Medium
    - tech_blog: Dev.to
    - all: All sources
    """
    return await search_by_source_category(query, source_category, category, format, api_key)


# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.utcnow().isoformat()
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "status_code": 500,
        "timestamp": datetime.utcnow().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="info"
    )
