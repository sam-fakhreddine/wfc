#!/usr/bin/env bash
#
# WFC Quick Start - Setup with sensible defaults (no prompts)
#

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEVCONTAINER_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$DEVCONTAINER_DIR")"

cd "$PROJECT_DIR"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║              WFC Quick Start                                  ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if .env exists
if [[ -f .devcontainer/.env ]]; then
    echo -e "${YELLOW}⚠  .devcontainer/.env file already exists${NC}"
    read -p "   Overwrite? (y/n): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${BLUE}Keeping existing .env${NC}"
    else
        cp .devcontainer/.env.example .devcontainer/.env
        echo -e "${GREEN}✓ .env created from template${NC}"
    fi
else
    cp .devcontainer/.env.example .devcontainer/.env
    echo -e "${GREEN}✓ .env created from template${NC}"
fi

# Create docker-compose.override.yml with current directory
if [[ ! -f .devcontainer/docker-compose.override.yml ]]; then
    cat > .devcontainer/docker-compose.override.yml <<EOF
services:
  app:
    volumes:
      # Mount current directory to /workspace/app
      - $(pwd):/workspace/app:cached
EOF
    echo -e "${GREEN}✓ docker-compose.override.yml created${NC}"
else
    echo -e "${YELLOW}⚠  docker-compose.override.yml already exists (keeping it)${NC}"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Quick setup complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "   ${BLUE}1.${NC} Edit .devcontainer/.env and add your ANTHROPIC_AUTH_TOKEN"
echo -e "      ${GREEN}ANTHROPIC_AUTH_TOKEN=sk-ant-your-key-here${NC}"
echo ""
echo -e "   ${BLUE}2.${NC} Start the container:"
echo -e "      ${GREEN}bash .devcontainer/scripts/start.sh build${NC}"
echo ""
echo -e "   ${BLUE}3.${NC} Open in VS Code:"
echo -e "      ${GREEN}code .${NC}"
echo -e "      Then: F1 → 'Dev Containers: Reopen in Container'"
echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}Tip: Use ${GREEN}bash .devcontainer/scripts/start.sh help${NC}${YELLOW} for all commands${NC}"
echo ""
