from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from enum import Enum


class OutputFormat(str, Enum):
    json = "json"
    csv = "csv"
    xml = "xml"


class OutputMode(str, Enum):
    response = "response"
    markdown_file = "markdown_file"
    json = "json"


class NewsCategory(str, Enum):
    technology = "technology"
    business = "business"
    sports = "sports"
    health = "health"
    entertainment = "entertainment"
    politics = "politics"
    science = "science"
    general = "general"


class NewsSource(str, Enum):
    google_search = "google_search"
    google_news = "google_news"
    bing_news = "bing_news"
    duckduckgo = "duckduckgo"
    medium = "medium"
    devto = "devto"
    bbc_news = "bbc_news"
    cnn = "cnn"
    detik = "detik"
    kompas = "kompas"


class NewsItem(BaseModel):
    title: str = Field(..., description="The headline or title of the news article")
    link: HttpUrl = Field(..., description="The URL to the full article")
    source_name: str = Field(..., description="The name of the news source")
    snippet: str = Field(..., description="A brief description or excerpt from the article")
    published_date: Optional[datetime] = Field(None, description="When the article was published")
    scraped_timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the article was scraped")


class SearchResponse(BaseModel):
    query: str = Field(..., description="The search query used")
    item_count: int = Field(..., description="Number of items returned")
    sources_searched: List[str] = Field(..., description="List of sources that were searched")
    results: List[NewsItem] = Field(..., description="The search results")


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="The topic or keyword to search for")
    sources: Optional[str] = Field(None, description="Comma-separated list of news sources")
    category: Optional[NewsCategory] = Field(None, description="News category filter")
    format: OutputFormat = Field(default=OutputFormat.json, description="Output format")


class ScrapeUrlRequest(BaseModel):
    url: HttpUrl = Field(..., description="The full URL of the article to scrape")
    output_mode: OutputMode = Field(default=OutputMode.response, description="How to return the scraped content")
    format: OutputFormat = Field(default=OutputFormat.json, description="Output format for response mode")


class ScrapeUrlResponse(BaseModel):
    source_url: str = Field(..., description="The original URL that was scraped")
    title: Optional[str] = Field(None, description="The title of the scraped article")
    author: Optional[str] = Field(None, description="The author of the article")
    published_date: Optional[datetime] = Field(None, description="When the article was published")
    content: Optional[str] = Field(None, description="The main content of the article")
    status: str = Field(..., description="Status of the scraping operation")
    markdown_content: Optional[str] = Field(None, description="The scraped content in markdown format")
    file_path: Optional[str] = Field(None, description="Path to the saved file if output_mode is markdown_file")


class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    status_code: int = Field(..., description="HTTP status code")
