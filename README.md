# Nexus Aggregator

An intelligent information-gathering engine that transforms internet noise into structured signals. A comprehensive FastAPI-based news aggregation API featuring 10 news sources, multiple output formats, advanced scraping capabilities, and containerized deployment.

## ✨ Key Features

- **10 News Sources**: Google Search/News, Bing News, DuckDuckGo, Medium, Dev.to, BBC, CNN, Detik, Kompas
- **Anti-Bot Protection**: Playwright browser automation for Google Search
- **Multiple Output Formats**: JSON, CSV, XML, Markdown
- **Category-Based Search**: Technology, Business, Sports, Health, Entertainment, Politics, Science
- **Priority-Based Results**: Intelligent source ranking and deduplication
- **API Key Authentication**: Secure Bearer token authentication
- **Comprehensive Documentation**: OpenAPI/Swagger integration
- **Production Ready**: Environment-based configuration and Docker deployment

## 🏗️ Project Structure

```text
scraping_app/
├── app/                          # Core application code
│   ├── api/                     # API endpoints
│   │   ├── endpoints.py         # Main API route handlers
│   │   └── __init__.py
│   ├── core/                    # Core functionality
│   │   ├── auth.py             # API key authentication
│   │   ├── utils.py            # Utility functions
│   │   └── __init__.py
│   ├── models/                  # Data models
│   │   ├── schemas.py          # Pydantic schemas (10 news sources)
│   │   └── __init__.py
│   ├── services/               # Business logic
│   │   ├── scraper.py          # News scraping services (10 scrapers)
│   │   └── __init__.py
│   └── main.py                 # FastAPI app initialization
├── config/                      # Configuration
│   └── settings.py             # Environment-based settings
├── docker/                      # Docker configuration
│   ├── Dockerfile              # Container definition
│   ├── docker-compose.yml      # Production deployment
│   └── docker-compose.dev.yml  # Development deployment
├── docs/                        # Documentation
│   ├── API_DOCUMENTATION.md    # Comprehensive API docs
│   ├── README.md               # Development guide
│   └── swagger-ui.html         # Interactive API docs
├── scripts/                     # Utility scripts
│   ├── demo-docs.sh           # Documentation demo
│   ├── docker-setup.sh        # Docker setup automation
│   ├── start.sh               # Application start script
│   └── validate-openapi.sh    # OpenAPI validation
├── tests/                       # Test files
│   └── test_api.py             # API tests
├── main.py                     # Application entry point
├── requirements.txt            # Python dependencies
├── openapi.yaml               # OpenAPI 3.0 specification
├── openapi.json              # JSON OpenAPI specification
├── .env.example              # Environment variables template
├── Makefile                  # Development commands
├── FIXES_IMPLEMENTED.md      # Recent improvements documentation
└── README.md                 # This file
```

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone and navigate to the project**:
   ```bash
   git clone <repository-url>
   cd scraping_app
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start development environment**:
   ```bash
   make docker-dev
   ```

4. **Access the API**:
   - API: http://localhost:8000
   - Documentation: http://localhost:8000/docs
   - Health check: http://localhost:8000/health

### Using Local Python Environment

1. **Create virtual environment**:
   ```bash
   make setup-local
   ```

2. **Activate environment and run**:
   ```bash
   source venv/bin/activate
   make dev
   ```

## 🐳 Docker Commands

| Command | Description |
|---------|-------------|
| `make docker-build` | Build Docker image |
| `make docker-dev` | Start development environment |
| `make docker-prod` | Start production environment |
| `make docker-stop` | Stop all containers |
| `make docker-clean` | Clean containers and images |
| `make docker-logs` | View container logs |

## 📝 Development Commands

| Command | Description |
|---------|-------------|
| `make help` | Show all available commands |
| `make venv` | Create virtual environment |
| `make install` | Install dependencies |
| `make dev` | Run development server |
| `make test` | Run API tests |
| `make format` | Format code with black |
| `make clean-python` | Clean Python cache files |

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# API Configuration
API_KEYS=nexus_dev_key_123,your_api_key_2
HOST=0.0.0.0
PORT=8000
DEBUG=true

# External API Keys
DEVTO_API_KEY=your_devto_api_key_here

# Scraping Configuration
DEFAULT_SCRAPING_LIMIT=10
REQUEST_TIMEOUT=10

# File Paths
SCRAPED_ARTICLES_DIR=scraped_articles
LOGS_DIR=logs

# User Agent
USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36
```

### Available News Sources

#### Search Engines & Aggregators
- **google_search** - Google Search with Playwright (anti-bot protection)
- **google_news** - Google News RSS feed aggregator
- **bing_news** - Bing News API search results
- **duckduckgo** - DuckDuckGo search engine results

#### Publishing Platforms
- **medium** - Medium articles with multi-strategy scraping
- **devto** - Dev.to articles using official API

#### International News
- **bbc_news** - BBC News articles and headlines
- **cnn** - CNN breaking news and articles

#### Indonesian News
- **detik** - Detik.com Indonesian news portal
- **kompas** - Kompas.com Indonesian news source

### Docker Development

The development environment includes:
- Hot reload for code changes
- Volume mounting for live development
- Separate development configuration
- Debug logging enabled

## 📖 API Documentation

### Authentication

All endpoints require API key authentication via Bearer token:

```bash
curl -H "Authorization: Bearer your_api_key" http://localhost:8000/api/v1/search?query=technology
```

### Main Endpoints

#### 1. Search News
```
GET /api/v1/search?query={query}&sources={sources}&category={category}&format={format}
```

**Parameters:**
- `query` (required): Search term
- `sources` (optional): Comma-separated source list
- `category` (optional): News category filter
- `format` (optional): Response format (json, csv, xml)

#### 2. Scrape URL
```
POST /api/v1/scrape-url
{
  "url": "https://example.com/article",
  "output_mode": "response"
}
```

#### 3. Available Sources
```
GET /api/v1/sources
```

#### 4. Available Categories
```
GET /api/v1/categories
```

### Response Formats

The API supports multiple output formats:
- **JSON**: Default structured response
- **CSV**: Comma-separated values for spreadsheets
- **XML**: XML format for integration
- **Markdown**: For scraped article content

## 🧪 Testing

### Run All Tests
```bash
make test
```

### Test Against Docker Container
```bash
# Start container first
make docker-dev

# Run tests
make docker-test
```

### Manual API Testing
```bash
# Health check
curl http://localhost:8000/health

# Search with API key
curl -H "Authorization: Bearer nexus_dev_key_123" \
     "http://localhost:8000/api/v1/search?query=artificial%20intelligence"
```

## 🏭 Production Deployment

### Docker Production
```bash
# Build and start production environment
make docker-prod

# Monitor logs
make docker-logs

# Scale if needed
cd docker && docker-compose up -d --scale nexus-aggregator=3
```

### Environment Configuration

For production, ensure:
- Strong API keys in environment variables
- Proper logging configuration
- Resource limits in docker-compose.yml
- SSL/TLS termination at reverse proxy
- Regular health checks

## 🔍 Architecture

### Component Overview

1. **FastAPI Application** (`main_new.py`): Entry point and routing
2. **API Layer** (`app/api/`): Request handling and validation
3. **Service Layer** (`app/services/`): Business logic and scraping
4. **Core Layer** (`app/core/`): Authentication and utilities
5. **Models** (`app/models/`): Data schemas and validation
6. **Configuration** (`config/`): Settings management

### Design Patterns

- **Separation of Concerns**: Clear layer separation
- **Dependency Injection**: FastAPI's dependency system
- **Factory Pattern**: Service initialization
- **Repository Pattern**: Data access abstraction

## 🐛 Troubleshooting

### Common Issues

1. **Port Already in Use**:
   ```bash
   make docker-stop
   docker ps  # Check for running containers
   ```

2. **Import Errors**:
   - Ensure all `__init__.py` files exist
   - Check Python path configuration
   - Verify virtual environment activation

3. **Container Build Failures**:
   ```bash
   make docker-clean
   make docker-build
   ```

4. **API Key Authentication**:
   - Verify `.env` file configuration
   - Check API key format in requests
   - Ensure Bearer token prefix

### Debug Mode

Enable debug logging:
```bash
export DEBUG=True
make dev
```

Or in Docker:
```bash
# Edit docker-compose.dev.yml
environment:
  - DEBUG=True
```

## 📚 Development

### Code Style

- Follow PEP 8 guidelines
- Use type hints where possible
- Document functions and classes
- Format code with black: `make format`

### Adding New Features

1. Create feature branch
2. Add code in appropriate layer:
   - API endpoints → `app/api/`
   - Business logic → `app/services/`
   - Data models → `app/models/`
3. Add tests in `tests/`
4. Update documentation
5. Test with Docker environment

### Contributing

1. Fork the repository
2. Create feature branch
3. Make changes following code style
4. Add tests for new functionality
5. Update documentation
6. Submit pull request

## 📄 License

This project is licensed under the MIT License. See LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- BeautifulSoup4 for HTML parsing
- Docker for containerization
- uvicorn for ASGI server implementation
