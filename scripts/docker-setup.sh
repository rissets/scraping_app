#!/bin/bash

# Nexus Aggregator - Docker Setup Script (Updated for new structure)

set -e

echo "🐳 Nexus Aggregator Docker Setup"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Use docker-compose or docker compose
DOCKER_COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
fi

# Function to build and start development environment
start_dev() {
    print_status "Starting development environment..."
    
    # Create necessary directories
    mkdir -p scraped_articles logs
    
    print_status "Building Docker image..."
    docker build -t nexus-aggregator:latest -f docker/Dockerfile .
    
    print_status "Starting development environment..."
    cd docker && $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml up -d
    
    print_success "Development environment started!"
    print_status "API available at: http://localhost:8000"
    print_status "API docs available at: http://localhost:8000/docs"
    print_status "View logs with: make docker-logs"
}

# Function to build and start production environment
start_prod() {
    print_status "Starting production environment..."
    
    # Create necessary directories
    mkdir -p scraped_articles logs
    
    print_status "Building Docker image..."
    docker build -t nexus-aggregator:latest -f docker/Dockerfile .
    
    print_status "Starting production environment..."
    cd docker && $DOCKER_COMPOSE_CMD up -d
    
    print_success "Production environment started!"
    print_status "API available at: http://localhost:8000"
    print_status "API docs available at: http://localhost:8000/docs"
    print_status "View logs with: make docker-logs"
}

# Function to stop containers
stop_containers() {
    print_status "Stopping Docker containers..."
    
    cd docker
    $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml down 2>/dev/null || true
    $DOCKER_COMPOSE_CMD down 2>/dev/null || true
    
    print_success "All containers stopped!"
}

# Function to clean up Docker resources
clean_docker() {
    print_warning "This will remove all containers, networks, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd docker
        $DOCKER_COMPOSE_CMD -f docker-compose.dev.yml down -v 2>/dev/null || true
        $DOCKER_COMPOSE_CMD down -v 2>/dev/null || true
        
        print_status "Removing Docker images..."
        docker rmi nexus-aggregator:latest 2>/dev/null || true
        
        print_success "Docker cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Function to show logs
show_logs() {
    if docker ps --format "table {{.Names}}" | grep -q "nexus-aggregator"; then
        cd docker && $DOCKER_COMPOSE_CMD logs -f
    else
        print_error "No running containers found!"
        exit 1
    fi
}

# Function to run tests
run_tests() {
    print_status "Running API tests against Docker container..."
    
    # Check if container is running
    if ! docker ps --format "table {{.Names}}" | grep -q "nexus-aggregator"; then
        print_error "No running containers found! Start the application first."
        exit 1
    fi
    
    # Wait for container to be ready
    print_status "Waiting for API to be ready..."
    for i in {1..30}; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "API is not responding after 30 seconds"
            exit 1
        fi
        sleep 1
    done
    
    # Run tests
    if [ -f "tests/test_api.py" ]; then
        python3 tests/test_api.py
    else
        print_error "Test file not found: tests/test_api.py"
        exit 1
    fi
}

# Main script logic
case "${1:-}" in
    "dev")
        start_dev
        ;;
    "prod")
        start_prod
        ;;
    "stop")
        stop_containers
        ;;
    "clean")
        clean_docker
        ;;
    "logs")
        show_logs
        ;;
    "test")
        run_tests
        ;;
    *)
        echo "Usage: $0 {dev|prod|stop|clean|logs|test}"
        echo ""
        echo "Commands:"
        echo "  dev   - Start development environment"
        echo "  prod  - Start production environment"
        echo "  stop  - Stop all containers"
        echo "  clean - Remove all containers and images"
        echo "  logs  - Show container logs"
        echo "  test  - Run API tests"
        exit 1
        ;;
esac
