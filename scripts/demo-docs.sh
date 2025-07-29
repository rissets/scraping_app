#!/bin/bash

# Demo Script for Nexus Aggregator API Documentation
# This script demonstrates the OpenAPI documentation features

set -e

echo "🚀 Nexus Aggregator API Documentation Demo"
echo "==========================================="

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if API server is running
echo -e "${BLUE}1. Checking API server status...${NC}"
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API server is running${NC}"
else
    echo "❌ API server not running. Start with: make docker-dev"
    exit 1
fi

# Show health endpoint
echo -e "${BLUE}2. Testing health endpoint...${NC}"
curl -s http://localhost:8000/health | jq

# Show OpenAPI spec info
echo -e "${BLUE}3. Getting OpenAPI specification info...${NC}"
API_INFO=$(curl -s http://localhost:8000/openapi.json | jq '.info')
echo "$API_INFO"

# List available endpoints
echo -e "${BLUE}4. Available API endpoints:${NC}"
curl -s http://localhost:8000/openapi.json | jq -r '.paths | keys[]' | while read path; do
    methods=$(curl -s http://localhost:8000/openapi.json | jq -r ".paths[\"$path\"] | keys[]")
    echo "  $path ($methods)"
done

# Show documentation URLs
echo -e "${BLUE}5. Documentation URLs:${NC}"
echo "  📖 Swagger UI:    http://localhost:8000/docs"
echo "  📚 ReDoc:         http://localhost:8000/redoc"  
echo "  🔧 OpenAPI JSON:  http://localhost:8000/openapi.json"
echo "  📄 Custom UI:     docs/swagger-ui.html"

# Show authentication info
echo -e "${BLUE}6. Authentication example:${NC}"
echo "  curl -H \"Authorization: Bearer your_api_key\" \\"
echo "       \"http://localhost:8000/api/v1/search?query=technology\""

# Show file structure
echo -e "${BLUE}7. Documentation files:${NC}"
echo "  📄 openapi.yaml          - OpenAPI spec (YAML format)"
echo "  📄 openapi.json          - OpenAPI spec (JSON format)"  
echo "  📄 docs/swagger-ui.html  - Custom Swagger UI"
echo "  📄 docs/API_DOCUMENTATION.md - Complete API documentation"
echo "  🔧 scripts/validate-openapi.sh - Validation script"

echo ""
echo -e "${GREEN}🎉 Demo complete! Your API documentation is ready to use.${NC}"
echo ""
echo "Next steps:"
echo "  1. Open http://localhost:8000/docs in your browser"
echo "  2. Use the 'Authorize' button to enter your API key"
echo "  3. Try the interactive API endpoints"
echo "  4. Check out docs/API_DOCUMENTATION.md for detailed usage"
