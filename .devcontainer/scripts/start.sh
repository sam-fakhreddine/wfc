#!/usr/bin/env bash
#
# WFC DevContainer Starter
#
# This script helps you start the WFC development container.
# It supports multiple methods: VS Code, Docker CLI, or detached mode.
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVCONTAINER_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$DEVCONTAINER_DIR")"

cd "$PROJECT_DIR"

echo -e "${CYAN}${BOLD}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}${BOLD}║              WFC DevContainer Starter                         ║${NC}"
echo -e "${CYAN}${BOLD}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ────────────────────────────────────────────────────────────────────────────────
# Check Prerequisites
# ────────────────────────────────────────────────────────────────────────────────
HAS_VSCODE=0
HAS_DEV_CONTAINERS=0

check_prerequisites() {
    local missing=0

    # Check Docker
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}✗ Docker not found${NC}"
        echo "  Install Docker from: https://docs.docker.com/get-docker/"
        missing=1
    else
        echo -e "${GREEN}✓${NC} Docker installed: $(docker --version | cut -d' ' -f3)"
    fi

    # Check Docker is running
    if ! docker info &> /dev/null; then
        echo -e "${RED}✗ Docker is not running${NC}"
        echo "  Start Docker Desktop or run: sudo systemctl start docker"
        missing=1
    else
        echo -e "${GREEN}✓${NC} Docker is running"
    fi

    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        echo -e "${RED}✗ Docker Compose not found${NC}"
        missing=1
    else
        echo -e "${GREEN}✓${NC} Docker Compose: $(docker compose version | cut -d' ' -f4)"
    fi

    # Check VS Code (optional)
    if command -v code &> /dev/null; then
        echo -e "${GREEN}✓${NC} VS Code installed: $(code --version | head -1)"
        HAS_VSCODE=1
    else
        echo -e "${YELLOW}⚠${NC}  VS Code not found (optional)"
        HAS_VSCODE=0
    fi

    # Check Dev Containers extension (optional)
    if [[ $HAS_VSCODE -eq 1 ]]; then
        if code --list-extensions 2>/dev/null | grep -q "ms-vscode-remote.remote-containers"; then
            echo -e "${GREEN}✓${NC} Dev Containers extension installed"
            HAS_DEV_CONTAINERS=1
        else
            echo -e "${YELLOW}⚠${NC}  Dev Containers extension not installed"
            echo "  Install: code --install-extension ms-vscode-remote.remote-containers"
            HAS_DEV_CONTAINERS=0
        fi
    fi

    echo ""

    if [[ $missing -eq 1 ]]; then
        echo -e "${RED}Please install missing prerequisites${NC}"
        exit 1
    fi
}

# ────────────────────────────────────────────────────────────────────────────────
# Display Usage
# ────────────────────────────────────────────────────────────────────────────────
show_usage() {
    cat << EOF
${BOLD}Usage:${NC}
  $(basename "$0") [METHOD]

${BOLD}Methods:${NC}
  ${CYAN}vscode${NC}      Open in VS Code with Dev Containers (recommended)
  ${CYAN}build${NC}       Build and start containers in background
  ${CYAN}attach${NC}      Attach to running devcontainer shell
  ${CYAN}stop${NC}        Stop all containers
  ${CYAN}clean${NC}       Stop and remove all containers and volumes
  ${CYAN}logs${NC}        Show logs from all services
  ${CYAN}status${NC}      Show status of all containers
  ${CYAN}help${NC}        Show this help message

${BOLD}Examples:${NC}
  $(basename "$0") vscode     # Open in VS Code (best experience)
  $(basename "$0") build      # Start containers in background
  $(basename "$0") attach     # Get shell access to container

${BOLD}Quick Start:${NC}
  1. Run: $(basename "$0") vscode
  2. VS Code will prompt "Reopen in Container"
  3. Wait for container to build (3-5 minutes first time)
  4. Start coding with WFC!

EOF
}

# ────────────────────────────────────────────────────────────────────────────────
# Start with VS Code
# ────────────────────────────────────────────────────────────────────────────────
start_vscode() {
    echo -e "${BLUE}► Opening in VS Code...${NC}"

    if [[ $HAS_VSCODE -ne 1 ]]; then
        echo -e "${RED}✗ VS Code not installed${NC}"
        echo "  Install from: https://code.visualstudio.com/"
        exit 1
    fi

    # Open project in VS Code
    code "$PROJECT_DIR"

    echo ""
    echo -e "${GREEN}✓ VS Code opened${NC}"
    echo ""
    echo -e "${BOLD}Next Steps:${NC}"
    echo "  1. In VS Code, press ${CYAN}Cmd+Shift+P${NC} (Mac) or ${CYAN}Ctrl+Shift+P${NC} (Linux/Windows)"
    echo "  2. Type: ${CYAN}Dev Containers: Reopen in Container${NC}"
    echo "  3. Press Enter"
    echo ""
    echo "  ${YELLOW}First build takes 3-5 minutes. Subsequent starts are much faster.${NC}"
    echo ""
}

# ────────────────────────────────────────────────────────────────────────────────
# Build and Start Containers
# ────────────────────────────────────────────────────────────────────────────────
start_build() {
    echo -e "${BLUE}► Building and starting WFC devcontainer...${NC}"
    echo ""

    # Build and start
    docker compose -f "$DEVCONTAINER_DIR/docker-compose.yml" up -d --build

    echo ""
    echo -e "${GREEN}✓ WFC devcontainer started${NC}"
    echo ""

    # Show status
    docker compose -f "$DEVCONTAINER_DIR/docker-compose.yml" ps

    echo ""
    echo -e "${BOLD}Container Access:${NC}"
    echo "  Attach:    $(basename "$0") attach"
    echo "  Logs:      $(basename "$0") logs"
    echo "  Status:    $(basename "$0") status"
    echo ""
}

# ────────────────────────────────────────────────────────────────────────────────
# Attach to Container
# ────────────────────────────────────────────────────────────────────────────────
attach_container() {
    echo -e "${BLUE}► Attaching to WFC devcontainer...${NC}"
    echo ""

    # Check if container is running
    if ! docker compose -f "$DEVCONTAINER_DIR/docker-compose.yml" ps | grep -q "wfc-devcontainer.*Up\|wfc-devcontainer.*running"; then
        echo -e "${YELLOW}⚠ Container not running${NC}"
        echo "  Start with: $(basename "$0") build"
        exit 1
    fi

    # Attach to container with zsh
    docker compose -f "$DEVCONTAINER_DIR/docker-compose.yml" exec app zsh || \
    docker compose -f "$DEVCONTAINER_DIR/docker-compose.yml" exec app bash

    echo ""
    echo -e "${GREEN}✓ Detached from container${NC}"
}

# ────────────────────────────────────────────────────────────────────────────────
# Stop Containers
# ────────────────────────────────────────────────────────────────────────────────
stop_containers() {
    echo -e "${BLUE}► Stopping WFC devcontainer...${NC}"
    echo ""

    docker compose -f "$DEVCONTAINER_DIR/docker-compose.yml" down

    echo ""
    echo -e "${GREEN}✓ WFC devcontainer stopped${NC}"
    echo ""
}

# ────────────────────────────────────────────────────────────────────────────────
# Clean Everything
# ────────────────────────────────────────────────────────────────────────────────
clean_all() {
    echo -e "${YELLOW}► Stopping and removing all containers and volumes...${NC}"
    echo ""
    read -p "This will delete all cached data. Continue? [y/N] " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted"
        exit 0
    fi

    docker compose -f "$DEVCONTAINER_DIR/docker-compose.yml" down -v

    echo ""
    echo -e "${GREEN}✓ All containers and volumes removed${NC}"
    echo ""
}

# ────────────────────────────────────────────────────────────────────────────────
# Show Logs
# ────────────────────────────────────────────────────────────────────────────────
show_logs() {
    echo -e "${BLUE}► Showing logs (Ctrl+C to exit)...${NC}"
    echo ""

    docker compose -f "$DEVCONTAINER_DIR/docker-compose.yml" logs -f
}

# ────────────────────────────────────────────────────────────────────────────────
# Show Status
# ────────────────────────────────────────────────────────────────────────────────
show_status() {
    echo -e "${BLUE}► WFC DevContainer Status${NC}"
    echo ""

    docker compose -f "$DEVCONTAINER_DIR/docker-compose.yml" ps

    echo ""
}

# ────────────────────────────────────────────────────────────────────────────────
# Main
# ────────────────────────────────────────────────────────────────────────────────
main() {
    # Check prerequisites
    check_prerequisites

    # Parse arguments
    local method="${1:-vscode}"

    case "$method" in
        vscode|code)
            start_vscode
            ;;
        build|up|start)
            start_build
            ;;
        attach|shell|sh)
            attach_container
            ;;
        stop|down)
            stop_containers
            ;;
        clean|destroy|remove)
            clean_all
            ;;
        logs|log)
            show_logs
            ;;
        status|ps)
            show_status
            ;;
        help|--help|-h)
            show_usage
            ;;
        *)
            echo -e "${RED}Unknown method: $method${NC}"
            echo ""
            show_usage
            exit 1
            ;;
    esac
}

main "$@"
