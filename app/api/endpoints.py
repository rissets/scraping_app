import os
import asyncio
from typing import List, Optional
from datetime import datetime
from fastapi import HTTPException, Depends, Response
from fastapi.responses import PlainTextResponse
import aiofiles

from app.models.schemas import (
    SearchRequest, SearchResponse, ScrapeUrlRequest, ScrapeUrlResponse, 
    ErrorResponse, NewsItem, OutputFormat, OutputMode, NewsCategory
)
from app.core.auth import api_key_auth
from app.services.scraper import search_news, article_scraper
from app.core.utils import convert_to_csv, convert_to_xml, format_markdown_content, generate_filename


async def search_news_endpoint(
    query: str,
    sources: Optional[str] = None,
    category: Optional[NewsCategory] = None,
    format: OutputFormat = OutputFormat.json,
    api_key: str = Depends(api_key_auth.validate_api_key)
):
    """
    Search for news articles across multiple sources.
    
    - **query**: The topic or keyword to search for (required)
    - **sources**: Comma-separated list of news sources (optional, defaults to all)
    - **category**: News category filter (optional) 
    - **format**: Output format - json, csv, or xml (default: json)
    """
    try:
        # Parse sources
        source_list = None
        if sources:
            source_list = [s.strip() for s in sources.split(',') if s.strip()]
        
        # Search for news
        results = await search_news(
            query=query,
            sources=source_list,
            category=category,
            limit=10
        )
        
        # Determine which sources were actually searched
        sources_searched = source_list if source_list else [
            'google_search', 'duckduckgo', 'google_news', 'bing_news', 
            'bbc_news', 'cnn', 'detik', 'kompas', 'medium', 'devto'
        ]
        
        # Create response
        search_response = SearchResponse(
            query=query,
            item_count=len(results),
            sources_searched=sources_searched,
            results=results
        )
        
        # Return in requested format
        if format == OutputFormat.json:
            return search_response
        elif format == OutputFormat.csv:
            csv_content = convert_to_csv(search_response)
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=news_search_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
        elif format == OutputFormat.xml:
            xml_content = convert_to_xml(search_response)
            return Response(
                content=xml_content,
                media_type="application/xml",
                headers={"Content-Disposition": f"attachment; filename=news_search_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xml"}
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching for news: {str(e)}"
        )


async def scrape_url_endpoint(
    request: ScrapeUrlRequest,
    api_key: str = Depends(api_key_auth.validate_api_key)
):
    """
    Scrape content from a specific URL and return it in markdown format.
    
    - **url**: The full URL of the article to scrape (required)
    - **output_mode**: How to return the content - 'response' or 'markdown_file' (default: response)
    """
    try:
        url = str(request.url)
        
        # Scrape the article
        article_data = article_scraper.scrape_article(url)
        
        if article_data['status'] == 'error':
            raise HTTPException(
                status_code=400,
                detail=f"Failed to scrape URL: {article_data.get('error', 'Unknown error')}"
            )
        
        # Format as markdown
        markdown_content = format_markdown_content(
            title=article_data.get('title', 'Untitled'),
            author=article_data.get('author'),
            date=article_data.get('publish_date'),
            content=article_data.get('content', '')
        )
        
        if request.output_mode == OutputMode.response:
            # Return markdown in response
            return ScrapeUrlResponse(
                source_url=url,
                status="success",
                markdown_content=markdown_content
            )
        
        elif request.output_mode == OutputMode.markdown_file:
            # Save to file
            filename = generate_filename(url)
            file_path = os.path.join("scraped_articles", filename)
            
            # Create directory if it doesn't exist
            os.makedirs("scraped_articles", exist_ok=True)
            
            # Save file
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(markdown_content)
            
            return ScrapeUrlResponse(
                source_url=url,
                status="success",
                file_path=file_path
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error scraping URL: {str(e)}"
        )


async def get_available_sources(api_key: str = Depends(api_key_auth.validate_api_key)):
    """Get list of available news sources."""
    return {
        "available_sources": [
            {
                "id": "google_search",
                "name": "Google Search",
                "description": "Google Search with news filter (priority source)",
                "category": "search_engine"
            },
            {
                "id": "duckduckgo",
                "name": "DuckDuckGo",
                "description": "DuckDuckGo search engine (Google alternative)",
                "category": "search_engine"
            },
            {
                "id": "google_news",
                "name": "Google News",
                "description": "Google News RSS feed",
                "category": "news_aggregator"
            },
            {
                "id": "bing_news", 
                "name": "Bing News",
                "description": "Bing News search results",
                "category": "news_aggregator"
            },
            {
                "id": "bbc_news",
                "name": "BBC News",
                "description": "British Broadcasting Corporation news",
                "category": "international_news"
            },
            {
                "id": "cnn",
                "name": "CNN",
                "description": "Cable News Network",
                "category": "international_news"
            },
            {
                "id": "detik",
                "name": "Detik",
                "description": "Indonesian news portal",
                "category": "national_news"
            },
            {
                "id": "kompas",
                "name": "Kompas",
                "description": "Indonesian news and media company",
                "category": "national_news"
            },
            {
                "id": "medium",
                "name": "Medium",
                "description": "Online publishing platform for articles and blogs",
                "category": "blog_platform"
            },
            {
                "id": "devto",
                "name": "Dev.to",
                "description": "Developer community and articles",
                "category": "tech_blog"
            }
        ]
    }


async def get_available_categories(api_key: str = Depends(api_key_auth.validate_api_key)):
    """Get list of available news categories."""
    return {
        "available_categories": [
            {"id": category.value, "name": category.value.title()} 
            for category in NewsCategory
        ]
    }


async def search_by_source_category(
    query: str,
    source_category: str,
    category: Optional[NewsCategory] = None,
    format: OutputFormat = OutputFormat.json,
    api_key: str = Depends(api_key_auth.validate_api_key)
):
    """
    Search for news articles by source category.
    
    - **query**: The topic or keyword to search for (required)
    - **source_category**: Category of sources - search_engine, news_aggregator, international_news, national_news, blog_platform, tech_blog
    - **category**: News category filter (optional)
    - **format**: Output format - json, csv, or xml (default: json)
    """
    try:
        # Map source categories to sources
        category_sources = {
            'search_engine': ['google_search', 'duckduckgo'],
            'news_aggregator': ['google_news', 'bing_news'],
            'international_news': ['bbc_news', 'cnn'],
            'national_news': ['detik', 'kompas'],
            'blog_platform': ['medium'],
            'tech_blog': ['devto'],
            'all': ['google_search', 'duckduckgo', 'google_news', 'bing_news', 'bbc_news', 'cnn', 'detik', 'kompas', 'medium', 'devto']
        }
        
        if source_category not in category_sources:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid source category. Available: {list(category_sources.keys())}"
            )
        
        source_list = category_sources[source_category]
        
        # Search for news
        results = await search_news(
            query=query,
            sources=source_list,
            category=category,
            limit=10
        )
        
        # Create response
        search_response = SearchResponse(
            query=query,
            item_count=len(results),
            sources_searched=source_list,
            results=results
        )
        
        # Return in requested format
        if format == OutputFormat.json:
            return search_response
        elif format == OutputFormat.csv:
            csv_content = convert_to_csv(search_response)
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=news_search_{source_category}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"}
            )
        elif format == OutputFormat.xml:
            xml_content = convert_to_xml(search_response)
            return Response(
                content=xml_content,
                media_type="application/xml", 
                headers={"Content-Disposition": f"attachment; filename=news_search_{source_category}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xml"}
            )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error searching for news: {str(e)}"
        )
