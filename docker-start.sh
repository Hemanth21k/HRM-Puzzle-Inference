#!/bin/bash

# AI Sudoku Solver - Docker Startup Script

set -e

echo "================================"
echo "AI Sudoku Solver - Docker Setup"
echo "================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check if running with appropriate permissions
if ! docker ps &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to Docker daemon${NC}"
    echo "Please make sure:"
    echo "  1. Docker is running"
    echo "  2. You have permission to run Docker (add user to docker group or use sudo)"
    exit 1
fi

echo -e "${GREEN}✓${NC} Docker is installed and running"

# Check for GPU support
echo ""
echo "Checking GPU support..."
if docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo -e "${GREEN}✓${NC} GPU support is available"
    USE_GPU=true
else
    echo -e "${YELLOW}⚠${NC} GPU support not available, will run in CPU mode"
    echo "To enable GPU support, install NVIDIA Container Toolkit:"
    echo "https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html"
    USE_GPU=false
fi

# Check for models directory
echo ""
echo "Checking for model files..."
if [ ! -d "checkpoints" ]; then
    echo -e "${YELLOW}⚠${NC} Creating models directory..."
    mkdir -p checkpoints/sudoku-1k
    echo "Please organize your model files in subdirectories:"
    echo "  - checkpoints/sudoku-1k/step_XXXXX.pt (or .pth, .ckpt, etc.)"
    echo "  - checkpoints/sudoku-1k/all_config.yaml"
    echo "  - checkpoints/other-game/checkpoint.pt"
    echo "  - checkpoints/other-game/all_config.yaml"
fi

if [ -z "$(find models -type f \( -name "*.pt" -o -name "*.pth" -o -name "*.ckpt" \))" ]; then
    echo -e "${YELLOW}⚠${NC} No checkpoint files found in checkpoints/"
    echo "Please add your model checkpoints before starting"
    echo "Supported formats: .pt, .pth, .ckpt"
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Parse command line arguments
REBUILD=false
DETACH=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild)
            REBUILD=true
            shift
            ;;
        -d|--detach)
            DETACH=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --rebuild     Rebuild Docker images before starting"
            echo "  -d, --detach  Run containers in background"
            echo "  -h, --help    Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build command
BUILD_CMD="docker-compose up"
if [ "$REBUILD" = true ]; then
    BUILD_CMD="$BUILD_CMD --build"
fi
if [ "$DETACH" = true ]; then
    BUILD_CMD="$BUILD_CMD -d"
fi

# Stop existing containers
echo ""
echo "Stopping any existing containers..."
docker-compose down 2>/dev/null || true

# Start services
echo ""
echo "Starting services..."
echo "Command: $BUILD_CMD"
echo ""

$BUILD_CMD

# If running in detached mode, show status
if [ "$DETACH" = true ]; then
    echo ""
    echo -e "${GREEN}Containers started successfully!${NC}"
    echo ""
    echo "Service URLs:"
    echo "  Frontend:  http://localhost"
    echo "  Backend:   http://localhost:8000"
    echo "  API Docs:  http://localhost:8000/docs"
    echo ""
    echo "Useful commands:"
    echo "  View logs:        docker-compose logs -f"
    echo "  Stop services:    docker-compose down"
    echo "  Restart services: docker-compose restart"
    echo "  View status:      docker-compose ps"
    echo ""
else
    echo ""
    echo "Press Ctrl+C to stop the services"
fi