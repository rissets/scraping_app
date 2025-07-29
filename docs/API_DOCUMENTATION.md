# Nexus Aggregator API Documentation

## 📖 Overview

The Nexus Aggregator API provides a comprehensive interface for searching and scraping news articles from multiple sources. This documentation covers all available endpoints, authentication, and usage examples.

## 🔗 Quick Links

- **Interactive API Docs**: Open `docs/swagger-ui.html` in your browser
- **OpenAPI Spec**: 
  - YAML: `openapi.yaml`
  - JSON: `openapi.json`
- **Base URL**: `http://localhost:8000` (development)

## 🚀 Getting Started

### 1. Start the API Server

```bash
# Using Docker Compose (recommended)
make docker-dev

# Or using Make commands
make run

# Or directly with uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Custom Docs**: Open `docs/swagger-ui.html` in browser

### 3. Authentication

All API endpoints (except health checks) require API key authentication:

```bash
# Example request
curl -H "Authorization: Bearer your_api_key_here" \
     "http://localhost:8000/api/v1/search?query=technology"
```

## 📋 API Endpoints

### Health Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/` | Root endpoint with API info | No |
| GET | `/health` | Health check status | No |

### News Search

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/search` | Search news articles across multiple sources | Yes |
| GET | `/api/v1/search-by-source-category` | Search by specific source and category | Yes |
| POST | `/api/v1/scrape-url` | Scrape article content from URL | Yes |

### Configuration

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/api/v1/sources` | Get available news sources | Yes |
| GET | `/api/v1/categories` | Get available categories | Yes |

## 💡 Usage Examples

### Search News Articles

```bash
# Basic search
curl -H "Authorization: Bearer your_api_key" \
     "http://localhost:8000/api/v1/search?query=artificial%20intelligence"

# Advanced search with filters
curl -H "Authorization: Bearer your_api_key" \
     "http://localhost:8000/api/v1/search?query=AI&sources=google_news,bing_news&category=technology&format=json"

# Export as CSV
curl -H "Authorization: Bearer your_api_key" \
     "http://localhost:8000/api/v1/search?query=crypto&format=csv" \
     -o news_results.csv

# Search specific source and category
curl -H "Authorization: Bearer your_api_key" \
     "http://localhost:8000/api/v1/search-by-source-category?query=AI&source=medium&category=technology"
```

### Scrape Article Content

```bash
# Scrape and return content
curl -X POST \
     -H "Authorization: Bearer your_api_key" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/article", "output_mode": "response"}' \
     http://localhost:8000/api/v1/scrape-url

# Scrape and save to file
curl -X POST \
     -H "Authorization: Bearer your_api_key" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://example.com/article", "output_mode": "markdown_file"}' \
     http://localhost:8000/api/v1/scrape-url
```

### Get Configuration

```bash
# List available sources
curl -H "Authorization: Bearer your_api_key" \
     http://localhost:8000/api/v1/sources

# List available categories
curl -H "Authorization: Bearer your_api_key" \
     http://localhost:8000/api/v1/categories
```

## 📊 Response Formats

### JSON Response (Default)

```json
{
  "query": "artificial intelligence",
  "item_count": 10,
  "sources_searched": ["google_news", "bing_news"],
  "results": [
    {
      "title": "AI Breakthrough in 2025",
      "link": "https://example.com/ai-news",
      "source_name": "Google News",
      "snippet": "Latest developments in AI technology...",
      "published_date": "2025-07-29T12:00:00Z",
      "scraped_timestamp": "2025-07-29T14:00:00Z"
    }
  ]
}
```

### CSV Export

```csv
title,link,source_name,snippet,published_date,scraped_timestamp
"AI Breakthrough in 2025","https://example.com/ai-news","Google News","Latest developments...","2025-07-29T12:00:00","2025-07-29T14:00:00"
```

### XML Export

```xml
<?xml version="1.0" encoding="UTF-8"?>
<search_results>
  <metadata>
    <query>artificial intelligence</query>
    <item_count>10</item_count>
  </metadata>
  <results>
    <news_item>
      <title>AI Breakthrough in 2025</title>
      <link>https://example.com/ai-news</link>
      <source_name>Google News</source_name>
    </news_item>
  </results>
</search_results>
```

## 🔒 Authentication

### API Key Format

The API uses Bearer token authentication. Include your API key in the Authorization header:

```
Authorization: Bearer your_api_key_here
```

### Getting an API Key

1. **Development**: Use any string for testing (e.g., `test-key-123`)
2. **Production**: Contact support@nexusaggregator.com
3. **Self-hosted**: Configure in your environment variables

## ⚡ Rate Limiting

- **Standard**: 100 requests per minute per API key
- **Burst**: 20 requests per second
- **Headers**: Rate limit info included in response headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1722262800
```

## 🎯 Categories & Sources

### Available Sources

#### Search Engines & Aggregators
- `google_search` - Google Search with Playwright (anti-bot protection)
- `google_news` - Google News RSS feed aggregator  
- `bing_news` - Bing News API search results
- `duckduckgo` - DuckDuckGo search engine results

#### Publishing Platforms
- `medium` - Medium articles with multi-strategy scraping
- `devto` - Dev.to articles using official API

#### International News
- `bbc_news` - BBC News articles and headlines
- `cnn` - CNN breaking news and articles

#### Indonesian News
- `detik` - Detik.com Indonesian news portal
- `kompas` - Kompas.com Indonesian news source

### Available Categories

- `technology` - Tech news and innovations
- `business` - Business and finance news
- `sports` - Sports updates and scores
- `health` - Health and medical news
- `entertainment` - Entertainment and celebrity news
- `politics` - Political news and updates
- `science` - Scientific discoveries and research
- `general` - General news and misc topics

### Available Sources

- `google_news` - Google News RSS feeds
- `bing_news` - Bing News search results

## 🛠️ Development Tools

### Generate API Client

Using the OpenAPI specification, you can generate client libraries:

```bash
# Python client
openapi-generator-cli generate -i openapi.yaml -g python -o ./clients/python

# JavaScript client
openapi-generator-cli generate -i openapi.yaml -g javascript -o ./clients/javascript

# Go client
openapi-generator-cli generate -i openapi.yaml -g go -o ./clients/go
```

### Validate API Spec

```bash
# Install swagger-codegen or openapi-generator
npm install -g @apidevtools/swagger-parser

# Validate the spec
swagger-parser validate openapi.yaml
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Test with authentication
curl -H "Authorization: Bearer test-key" \
     http://localhost:8000/api/v1/sources
```

## 🐛 Error Handling

All errors follow a consistent format:

```json
{
  "error": "Invalid API key",
  "detail": "The provided API key is not valid or has expired",
  "status_code": 401,
  "timestamp": "2025-07-29T14:00:00Z"
}
```

### Common Error Codes

- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (invalid/missing API key)
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## 📚 Integration Examples

### Python Integration

```python
import requests

API_KEY = "your_api_key_here"
BASE_URL = "http://localhost:8000"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Search news
response = requests.get(
    f"{BASE_URL}/api/v1/search",
    headers=headers,
    params={"query": "AI", "category": "technology"}
)

news_data = response.json()
print(f"Found {news_data['item_count']} articles")
```

### JavaScript Integration

```javascript
const API_KEY = 'your_api_key_here';
const BASE_URL = 'http://localhost:8000';

const headers = {
    'Authorization': `Bearer ${API_KEY}`,
    'Content-Type': 'application/json'
};

// Search news
fetch(`${BASE_URL}/api/v1/search?query=AI&category=technology`, {
    headers: headers
})
.then(response => response.json())
.then(data => {
    console.log(`Found ${data.item_count} articles`);
    data.results.forEach(article => {
        console.log(`- ${article.title}`);
    });
});
```

### curl Examples

```bash
# Health check
curl -s http://localhost:8000/health | jq

# Search with pretty printing
curl -s -H "Authorization: Bearer test-key" \
     "http://localhost:8000/api/v1/search?query=technology" | jq

# Download CSV
curl -H "Authorization: Bearer test-key" \
     "http://localhost:8000/api/v1/search?query=AI&format=csv" \
     -o results.csv
```

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
API_KEY=your_secret_api_key
DEBUG=true
LOG_LEVEL=info

# Server Configuration
HOST=0.0.0.0
PORT=8000
WORKERS=4

# External Services
USER_AGENT="Nexus-Aggregator/1.0"
REQUEST_TIMEOUT=30
```

### Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'
services:
  nexus-aggregator:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_KEY=your_api_key
      - DEBUG=false
    volumes:
      - ./scraped_articles:/app/scraped_articles
```

## 📖 Additional Resources

- **OpenAPI Specification**: [OpenAPI 3.0.3](https://swagger.io/specification/)
- **FastAPI Documentation**: [FastAPI Docs](https://fastapi.tiangolo.com/)
- **Swagger UI**: [Swagger Documentation](https://swagger.io/tools/swagger-ui/)
- **ReDoc**: [ReDoc Documentation](https://redocly.github.io/redoc/)

## 🤝 Support

- **Issues**: Create an issue in the project repository
- **Email**: support@nexusaggregator.com
- **Documentation**: https://docs.nexusaggregator.com

---

*Last updated: July 29, 2025*
