#!/bin/bash

# OpenAPI Specification Validation Script
# This script validates the OpenAPI specification files

set -e

echo "🔍 Validating OpenAPI Specification..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if required tools are installed
check_dependencies() {
    echo "📦 Checking dependencies..."
    
    # Check for swagger-codegen or openapi-generator
    if ! command -v swagger-codegen &> /dev/null && ! command -v openapi-generator-cli &> /dev/null; then
        echo -e "${YELLOW}Warning: Neither swagger-codegen nor openapi-generator-cli found${NC}"
        echo "Install one of them for full validation:"
        echo "  npm install -g @openapitools/openapi-generator-cli"
        echo "  # or"
        echo "  npm install -g swagger-codegen"
        VALIDATOR_AVAILABLE=false
    else
        VALIDATOR_AVAILABLE=true
    fi
    
    # Check for jq
    if ! command -v jq &> /dev/null; then
        echo -e "${YELLOW}Warning: jq not found. JSON validation will be limited${NC}"
        JQ_AVAILABLE=false
    else
        JQ_AVAILABLE=true
    fi
    
    # Check for curl
    if ! command -v curl &> /dev/null; then
        echo -e "${RED}Error: curl is required but not installed${NC}"
        exit 1
    fi
}

# Validate JSON syntax
validate_json() {
    echo "🔧 Validating JSON syntax..."
    
    if [ "$JQ_AVAILABLE" = true ]; then
        if jq empty openapi.json 2>/dev/null; then
            echo -e "${GREEN}✅ JSON syntax is valid${NC}"
        else
            echo -e "${RED}❌ Invalid JSON syntax in openapi.json${NC}"
            return 1
        fi
    else
        # Basic JSON validation using python
        if python3 -c "import json; json.load(open('openapi.json'))" 2>/dev/null; then
            echo -e "${GREEN}✅ JSON syntax is valid${NC}"
        else
            echo -e "${RED}❌ Invalid JSON syntax in openapi.json${NC}"
            return 1
        fi
    fi
}

# Validate YAML syntax
validate_yaml() {
    echo "🔧 Validating YAML syntax..."
    
    # Use the correct Python path
    PYTHON_PATH="/home/haris/.pyenv/versions/3.12.3/bin/python"
    
    if [ -f "$PYTHON_PATH" ]; then
        if $PYTHON_PATH -c "import yaml; yaml.safe_load(open('openapi.yaml'))" 2>/dev/null; then
            echo -e "${GREEN}✅ YAML syntax is valid${NC}"
        else
            echo -e "${RED}❌ Invalid YAML syntax in openapi.yaml${NC}"
            return 1
        fi
    else
        # Fallback to system python
        if python3 -c "import yaml; yaml.safe_load(open('openapi.yaml'))" 2>/dev/null; then
            echo -e "${GREEN}✅ YAML syntax is valid${NC}"
        else
            echo -e "${RED}❌ Invalid YAML syntax in openapi.yaml${NC}"
            return 1
        fi
    fi
}

# Validate OpenAPI specification
validate_openapi_spec() {
    echo "🔧 Validating OpenAPI specification..."
    
    if [ "$VALIDATOR_AVAILABLE" = true ]; then
        if command -v openapi-generator-cli &> /dev/null; then
            if openapi-generator-cli validate -i openapi.yaml 2>/dev/null; then
                echo -e "${GREEN}✅ OpenAPI specification is valid${NC}"
            else
                echo -e "${RED}❌ OpenAPI specification validation failed${NC}"
                return 1
            fi
        elif command -v swagger-codegen &> /dev/null; then
            if swagger-codegen validate -i openapi.yaml 2>/dev/null; then
                echo -e "${GREEN}✅ OpenAPI specification is valid${NC}"
            else
                echo -e "${RED}❌ OpenAPI specification validation failed${NC}"
                return 1
            fi
        fi
    else
        echo -e "${YELLOW}⚠️ Skipping OpenAPI validation (validator not available)${NC}"
    fi
}

# Check file consistency
check_file_consistency() {
    echo "🔧 Checking file consistency..."
    
    PYTHON_PATH="/home/haris/.pyenv/versions/3.12.3/bin/python"
    
    if [ "$JQ_AVAILABLE" = true ]; then
        # Extract titles and compare
        JSON_TITLE=$(jq -r '.info.title' openapi.json 2>/dev/null || echo "")
        
        if [ -f "$PYTHON_PATH" ]; then
            YAML_TITLE=$($PYTHON_PATH -c "import yaml; print(yaml.safe_load(open('openapi.yaml'))['info']['title'])" 2>/dev/null || echo "")
        else
            YAML_TITLE=$(python3 -c "import yaml; print(yaml.safe_load(open('openapi.yaml'))['info']['title'])" 2>/dev/null || echo "")
        fi
        
        if [ "$JSON_TITLE" = "$YAML_TITLE" ] && [ -n "$JSON_TITLE" ]; then
            echo -e "${GREEN}✅ JSON and YAML files are consistent${NC}"
        else
            echo -e "${RED}❌ JSON and YAML files have inconsistent titles${NC}"
            echo "JSON title: $JSON_TITLE"
            echo "YAML title: $YAML_TITLE"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️ Skipping consistency check (jq not available)${NC}"
    fi
}

# Test API server (if running)
test_api_server() {
    echo "🔧 Testing API server connectivity..."
    
    if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ API server is running and responsive${NC}"
        
        # Test OpenAPI endpoint
        if curl -s -f http://localhost:8000/openapi.json > /dev/null 2>&1; then
            echo -e "${GREEN}✅ OpenAPI endpoint is accessible${NC}"
        else
            echo -e "${YELLOW}⚠️ OpenAPI endpoint not accessible${NC}"
        fi
        
        # Test docs endpoint
        if curl -s -f http://localhost:8000/docs > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Swagger UI is accessible${NC}"
        else
            echo -e "${YELLOW}⚠️ Swagger UI not accessible${NC}"
        fi
        
    else
        echo -e "${YELLOW}⚠️ API server not running (start with: make docker-dev)${NC}"
    fi
}

# Generate client code (if validator available)
test_client_generation() {
    echo "🔧 Testing client code generation..."
    
    if [ "$VALIDATOR_AVAILABLE" = true ] && command -v openapi-generator-cli &> /dev/null; then
        # Create temporary directory
        TEMP_DIR=$(mktemp -d)
        
        echo "Generating Python client..."
        if openapi-generator-cli generate \
            -i openapi.yaml \
            -g python \
            -o "$TEMP_DIR/python-client" \
            --skip-validate-spec > /dev/null 2>&1; then
            echo -e "${GREEN}✅ Python client generation successful${NC}"
        else
            echo -e "${RED}❌ Python client generation failed${NC}"
        fi
        
        echo "Generating JavaScript client..."
        if openapi-generator-cli generate \
            -i openapi.yaml \
            -g javascript \
            -o "$TEMP_DIR/js-client" \
            --skip-validate-spec > /dev/null 2>&1; then
            echo -e "${GREEN}✅ JavaScript client generation successful${NC}"
        else
            echo -e "${RED}❌ JavaScript client generation failed${NC}"
        fi
        
        # Cleanup
        rm -rf "$TEMP_DIR"
    else
        echo -e "${YELLOW}⚠️ Skipping client generation (openapi-generator-cli not available)${NC}"
    fi
}

# Main validation function
main() {
    echo "🚀 Starting OpenAPI Specification Validation"
    echo "============================================="
    
    # Check if files exist
    if [ ! -f "openapi.yaml" ] || [ ! -f "openapi.json" ]; then
        echo -e "${RED}❌ OpenAPI specification files not found${NC}"
        echo "Expected files: openapi.yaml, openapi.json"
        exit 1
    fi
    
    VALIDATION_PASSED=true
    
    # Run all validations
    check_dependencies
    
    if ! validate_json; then
        VALIDATION_PASSED=false
    fi
    
    if ! validate_yaml; then
        VALIDATION_PASSED=false
    fi
    
    if ! validate_openapi_spec; then
        VALIDATION_PASSED=false
    fi
    
    if ! check_file_consistency; then
        VALIDATION_PASSED=false
    fi
    
    test_api_server
    test_client_generation
    
    echo ""
    echo "============================================="
    
    if [ "$VALIDATION_PASSED" = true ]; then
        echo -e "${GREEN}🎉 All validations passed!${NC}"
        echo ""
        echo "Next steps:"
        echo "  • Start API server: make docker-dev"
        echo "  • View docs: http://localhost:8000/docs"
        echo "  • Open custom UI: docs/swagger-ui.html"
        exit 0
    else
        echo -e "${RED}❌ Some validations failed${NC}"
        echo ""
        echo "Please fix the issues above and run the validation again."
        exit 1
    fi
}

# Run main function
main "$@"
