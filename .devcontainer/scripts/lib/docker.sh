#!/usr/bin/env bash
#
# Docker prerequisite checks
# Verifies Docker, Docker Compose, and daemon status
#

# Check if all Docker prerequisites are met
# Returns 0 if all checks pass, 1 if any fail
check_docker_prerequisites() {
    local missing_deps=0

    echo -e "${GREEN}Step 1: Checking prerequisites...${NC}"
    echo ""

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}  Docker not found${NC}"
        echo "   Install from: https://docs.docker.com/get-docker/"
        missing_deps=1
    else
        echo -e "${GREEN}✓${NC} Docker found: $(docker --version)"
    fi

    # Check Docker Compose
    if ! command -v docker compose &> /dev/null; then
        if ! command -v docker-compose &> /dev/null; then
            echo -e "${RED}  Docker Compose not found${NC}"
            echo "   Install from: https://docs.docker.com/compose/install/"
            missing_deps=1
        else
            echo -e "${GREEN}✓${NC} Docker Compose found: $(docker-compose --version)"
        fi
    else
        echo -e "${GREEN}✓${NC} Docker Compose found: $(docker compose version)"
    fi

    # Check if Docker is running
    if ! docker info &> /dev/null; then
        echo -e "${YELLOW}  Docker daemon not running${NC}"
        echo "   Please start Docker Desktop and try again"
        missing_deps=1
    else
        echo -e "${GREEN}✓${NC} Docker daemon is running"
    fi

    # Check Git (optional but recommended)
    if ! command -v git &> /dev/null; then
        echo -e "${YELLOW}  Git not found (optional but recommended)${NC}"
    else
        echo -e "${GREEN}✓${NC} Git found: $(git --version)"
    fi

    echo ""

    if [[ $missing_deps -eq 1 ]]; then
        echo -e "${RED}Missing required dependencies. Please install them and try again.${NC}"
        return 1
    fi

    return 0
}
