#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🐳 IDI Docker Setup Script${NC}"
echo "=========================="

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
        exit 1
    fi
}

# Function to create necessary directories
create_directories() {
    echo -e "${YELLOW}📁 Creating necessary directories...${NC}"
    
    # Create main directories
    mkdir -p media/uploads 2>/dev/null || {
        echo -e "${RED}❌ Cannot create media directories. You may need to run:${NC}"
        echo "  sudo mkdir -p media/uploads"
        echo "  sudo chown -R \$(id -u):\$(id -g) media/"
        return 1
    }
    mkdir -p staticfiles 2>/dev/null || true
    
    # Create media upload subdirectories based on models
    mkdir -p media/uploads/team 2>/dev/null || true
    mkdir -p media/uploads/team/shapes 2>/dev/null || true
    mkdir -p media/uploads/projects/thumbnails 2>/dev/null || true
    mkdir -p media/uploads/testimonials 2>/dev/null || true
    mkdir -p media/uploads/programs 2>/dev/null || true
    mkdir -p media/uploads/programs/brochures 2>/dev/null || true
    mkdir -p media/uploads/partners 2>/dev/null || true
    mkdir -p media/uploads/clients 2>/dev/null || true
    
    # Set proper permissions for media directory (if writable)
    if [ -w media ]; then
        # Set directories to 755 (executable for traversal) and files to 644 (not executable)
        find media -type d -exec chmod 755 {} \; 2>/dev/null || true
        find media -type f -exec chmod 644 {} \; 2>/dev/null || true
        echo -e "${GREEN}✅ Directories created with proper permissions${NC}"
    else
        echo -e "${YELLOW}⚠️  Created directories but cannot set permissions. You may need to run:${NC}"
        echo "  sudo chown -R \$(id -u):\$(id -g) media/"
        echo "  find media -type d -exec chmod 755 {} \;"
        echo "  find media -type f -exec chmod 644 {} \;"
    fi
}

# Function to build Docker image
build_image() {
    echo -e "${YELLOW}🔨 Building Docker image...${NC}"
    
    if docker build -t idi .; then
        echo -e "${GREEN}✅ Docker image built successfully${NC}"
    else
        echo -e "${RED}❌ Failed to build Docker image${NC}"
        exit 1
    fi
}

# Function to stop existing container
stop_existing() {
    echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
    
    # Stop and remove existing container if it exists
    docker stop idi-container 2>/dev/null || true
    docker rm idi-container 2>/dev/null || true
    
    echo -e "${GREEN}✅ Existing containers stopped${NC}"
}

# Function to run container
run_container() {
    echo -e "${YELLOW}🚀 Starting new container...${NC}"
    
    # Get current user ID and group ID
    USER_ID=$(id -u)
    GROUP_ID=$(id -g)
    
    # Run the container with proper volume mounts and user mapping
    if docker run -d \
        --name idi-container \
        -p 8000:8000 \
        -v "$(pwd)/media:/app/media" \
        -v "$(pwd)/staticfiles:/app/staticfiles" \
        --user "${USER_ID}:${GROUP_ID}" \
        idi; then
        echo -e "${GREEN}✅ Container started successfully${NC}"
    else
        echo -e "${RED}❌ Failed to start container${NC}"
        exit 1
    fi
}

# Function to run with docker-compose (alternative)
run_compose() {
    echo -e "${YELLOW}🚀 Starting with Docker Compose...${NC}"
    
    if docker-compose up -d web; then
        echo -e "${GREEN}✅ Services started with Docker Compose${NC}"
    else
        echo -e "${RED}❌ Failed to start with Docker Compose${NC}"
        exit 1
    fi
}

# Function to show container status
show_status() {
    echo -e "${YELLOW}📊 Container Status:${NC}"
    echo "===================="
    
    # Show running containers
    docker ps --filter "name=idi-container" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    echo ""
    echo -e "${GREEN}🌐 Application should be available at: http://localhost:8000${NC}"
    echo -e "${GREEN}📱 Admin panel at: http://localhost:8000/admin (admin/admin123)${NC}"
    
    echo ""
    echo "📋 Useful commands:"
    echo "  View logs:     docker logs -f idi-container"
    echo "  Stop container: docker stop idi-container"
    echo "  Remove container: docker rm idi-container"
    echo "  Shell access:  docker exec -it idi-container bash"
}

# Function to fix permissions (if needed)
fix_permissions() {
    echo -e "${YELLOW}🔧 Fixing media directory permissions...${NC}"
    
    # Create directories first if they don't exist
    echo "Creating missing directories..."
    sudo mkdir -p media/uploads/team
    sudo mkdir -p media/uploads/team/shapes
    sudo mkdir -p media/uploads/projects/thumbnails
    sudo mkdir -p media/uploads/testimonials
    sudo mkdir -p media/uploads/programs
    sudo mkdir -p media/uploads/programs/brochures
    sudo mkdir -p media/uploads/partners
    sudo mkdir -p media/uploads/clients
    
    # Fix local media directory permissions
    sudo chown -R $(id -u):$(id -g) media/ 2>/dev/null || {
        echo -e "${RED}❌ Could not change ownership${NC}"
        return 1
    }
    
    # Set directories to 755 and files to 644
    find media -type d -exec chmod 755 {} \;
    find media -type f -exec chmod 644 {} \;
    
    echo -e "${GREEN}✅ All directories created and permissions fixed${NC}"
}

# Main script execution
main() {
    check_docker
    create_directories
    
    # Parse command line arguments
    case "${1:-run}" in
        "build")
            build_image
            ;;
        "run")
            build_image
            stop_existing
            run_container
            show_status
            ;;
        "compose")
            build_image
            run_compose
            show_status
            ;;
        "stop")
            stop_existing
            ;;
        "fix-permissions")
            fix_permissions
            ;;
        "status")
            show_status
            ;;
        *)
            echo "Usage: $0 {build|run|compose|stop|fix-permissions|status}"
            echo ""
            echo "Commands:"
            echo "  build           - Build Docker image only"
            echo "  run             - Build and run container (default)"
            echo "  compose         - Use Docker Compose"
            echo "  stop            - Stop and remove container"
            echo "  fix-permissions - Fix media directory permissions"
            echo "  status          - Show container status"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"