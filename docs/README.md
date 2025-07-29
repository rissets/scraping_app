# 📚 Nexus Aggregator API Documentation

## 🎯 Overview

Nexus Aggregator menyediakan dokumentasi API yang lengkap menggunakan OpenAPI 3.0.3 specification dengan berbagai format dan tools untuk memudahkan development dan integrasi.

## 📋 Quick Links

| Resource | URL | Description |
|----------|-----|-------------|
| **Swagger UI** | http://localhost:8000/docs | Interactive API documentation |
| **ReDoc** | http://localhost:8000/redoc | Alternative documentation UI |
| **OpenAPI JSON** | http://localhost:8000/openapi.json | OpenAPI spec (JSON format) |
| **Custom UI** | docs/swagger-ui.html | Enhanced custom documentation |

## 📁 Documentation Files

```
docs/
├── swagger-ui.html          # Enhanced Swagger UI with custom styling
├── API_DOCUMENTATION.md     # Complete API documentation guide
└── README.md               # This file

openapi.yaml                # OpenAPI specification (YAML)
openapi.json                # OpenAPI specification (JSON)

scripts/
├── validate-openapi.sh     # Validation script for OpenAPI specs
└── demo-docs.sh           # Documentation demo script
```

## 🚀 Quick Start

### 1. Start API Server

```bash
# Using Docker (recommended)
make docker-dev

# Or using Make
make dev

# Or directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Access Documentation

```bash
# Open Swagger UI in browser
make docs-serve

# Or visit manually
open http://localhost:8000/docs
```

### 3. Validate Documentation

```bash
# Run validation checks
make docs-validate

# Run demo
make docs-demo
```

## 🛠️ Available Commands

| Command | Description |
|---------|-------------|
| `make docs-validate` | Validate OpenAPI specification |
| `make docs-demo` | Run interactive documentation demo |
| `make docs-serve` | Open documentation in browser |
| `make docs-generate` | Generate client libraries |

## 🔑 Authentication

Semua endpoint API (kecuali health checks) memerlukan API key authentication:

```bash
# Example request
curl -H "Authorization: Bearer your_api_key_here" \
     "http://localhost:8000/api/v1/search?query=technology"
```

## 🎨 Features

### ✅ Interactive Documentation
- **Swagger UI**: Test API endpoints langsung dari browser
- **ReDoc**: Documentation yang clean dan responsive
- **Custom UI**: Enhanced interface dengan styling kustom

### ✅ Multiple Formats
- **YAML**: `openapi.yaml` - Human-readable format
- **JSON**: `openapi.json` - Machine-readable format
- **Live**: `/openapi.json` endpoint dari API server

### ✅ Validation & Testing
- **Syntax validation**: YAML dan JSON format checking
- **Consistency check**: Memastikan YAML dan JSON sync
- **API connectivity**: Test endpoint accessibility
- **Client generation**: Support untuk generate client libraries

### ✅ Comprehensive Coverage
- **All endpoints**: Search, scrape, configuration
- **Authentication**: API key dengan Bearer token
- **Error handling**: Consistent error response format
- **Examples**: Request/response examples untuk setiap endpoint

## 📖 API Endpoints Overview

### Health & Info
- `GET /` - Root endpoint dengan API info
- `GET /health` - Health check status

### News Operations
- `GET /api/v1/search` - Search news articles
- `POST /api/v1/scrape-url` - Scrape article content

### Configuration
- `GET /api/v1/sources` - Get available news sources
- `GET /api/v1/categories` - Get available categories

## 🔧 Development

### Generate Client Libraries

```bash
# Install openapi-generator-cli
npm install -g @openapitools/openapi-generator-cli

# Generate clients
make docs-generate

# Clients will be created in:
# - clients/python/    (Python client)
# - clients/javascript/ (JavaScript client)
```

### Custom Documentation

Edit `docs/swagger-ui.html` untuk customisasi:
- Styling dan branding
- Environment selector
- Authentication helpers
- Additional documentation links

### Validation Script

`scripts/validate-openapi.sh` melakukan:
- JSON syntax validation
- YAML syntax validation  
- OpenAPI spec validation (jika tool tersedia)
- File consistency checking
- API server connectivity testing

## 🎯 Usage Examples

### Basic API Testing

```bash
# Health check
curl http://localhost:8000/health

# Search news (with auth)
curl -H "Authorization: Bearer test-key" \
     "http://localhost:8000/api/v1/search?query=AI&category=technology"

# Get sources
curl -H "Authorization: Bearer test-key" \
     http://localhost:8000/api/v1/sources
```

### Documentation Testing

```bash
# Validate all specs
./scripts/validate-openapi.sh

# Run interactive demo
./scripts/demo-docs.sh

# Check API documentation
curl -s http://localhost:8000/openapi.json | jq '.info'
```

## 🌐 Browser Access

1. **Swagger UI** - http://localhost:8000/docs
   - Interactive API testing
   - Built-in authentication
   - Request/response examples

2. **ReDoc** - http://localhost:8000/redoc
   - Clean documentation layout
   - Easy navigation
   - Mobile-friendly

3. **Custom UI** - `docs/swagger-ui.html`
   - Enhanced styling
   - Environment switching
   - Additional features

## 📝 Documentation Maintenance

### Update OpenAPI Spec

1. Edit `openapi.yaml` (primary source)
2. Regenerate `openapi.json` if needed
3. Run validation: `make docs-validate`
4. Test in browser: `make docs-serve`

### Add New Endpoints

1. Add endpoint definition in `openapi.yaml`
2. Include proper schemas and examples
3. Add authentication requirements
4. Update this README if needed
5. Validate and test

## 🎉 Success Metrics

✅ **Validation passed**: JSON, YAML, dan consistency checks  
✅ **API responsive**: Health dan OpenAPI endpoints accessible  
✅ **Documentation live**: Swagger UI dan ReDoc working  
✅ **Authentication ready**: Bearer token auth configured  
✅ **Examples complete**: All endpoints have working examples  

## 🔗 Resources

- [OpenAPI 3.0.3 Specification](https://swagger.io/specification/)
- [Swagger UI Documentation](https://swagger.io/tools/swagger-ui/)
- [ReDoc Documentation](https://redocly.github.io/redoc/)
- [FastAPI OpenAPI Support](https://fastapi.tiangolo.com/tutorial/metadata/)

---

*Generated for Nexus Aggregator v1.0.0 - July 29, 2025*
