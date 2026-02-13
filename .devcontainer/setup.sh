#!/usr/bin/env bash
#
# WFC DevContainer Setup Script (Linux/Mac)
#
# This script sets up the dev environment on the host machine
# and prepares the .env file with user-specific configuration.
#
# Architecture: Modular design with single-responsibility modules
# See scripts/lib/ for individual modules
#

set -euo pipefail

# Get script directory for sourcing modules
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Source all library modules
source "$SCRIPT_DIR/scripts/lib/colors.sh"
source "$SCRIPT_DIR/scripts/lib/validate.sh"
source "$SCRIPT_DIR/scripts/lib/docker.sh"
source "$SCRIPT_DIR/scripts/lib/config.sh"
source "$SCRIPT_DIR/scripts/lib/mounts.sh"

# ════════════════════════════════════════════════════════════════════════════════
# Main Setup Workflow
# ════════════════════════════════════════════════════════════════════════════════

echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  WFC DevContainer Setup${NC}"
echo -e "${BLUE}  World Fucking Class Development Environment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""

# Step 1: Check Docker prerequisites
if ! check_docker_prerequisites; then
    exit 1
fi

# Step 2: Collect user configuration
collect_user_configuration

# Step 3: Generate .env file
generate_env_file

# Step 4: Collect folder mount configuration
collect_mount_configuration

# Step 5: Generate docker-compose.override.yml
generate_mount_config

# ────────────────────────────────────────────────────────────────────────────────
# Build and start container
# ────────────────────────────────────────────────────────────────────────────────

echo -e "${GREEN}Step 5: Build and start container${NC}"
echo ""
echo "This will:"
echo "  1. Build the Docker image (may take 3-5 minutes first time)"
echo "  2. Start the devcontainer"
echo "  3. Initialize the firewall in ${FIREWALL_MODE} mode"
echo ""

if prompt_yes_no "Proceed with build and startup?"; then
    echo ""
    echo "Building Docker image..."
    docker compose -f .devcontainer/docker-compose.yml -f .devcontainer/docker-compose.override.yml build

    echo ""
    echo "Starting container..."
    docker compose -f .devcontainer/docker-compose.yml -f .devcontainer/docker-compose.override.yml up -d

    echo ""
    echo -e "${GREEN}✓${NC} Container is starting!"
    echo ""
    echo "Wait a few seconds for services to initialize..."
    sleep 5

    # Show status
    docker compose -f .devcontainer/docker-compose.yml ps
fi

# ────────────────────────────────────────────────────────────────────────────────
# Setup complete
# ────────────────────────────────────────────────────────────────────────────────

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Setup Complete! ${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Next steps:"
echo ""
echo "1. Open in VS Code:"
echo "   code ."
echo ""
echo "2. When prompted, click 'Reopen in Container'"
echo ""
echo "3. Or manually attach:"
echo "   - F1 → 'Dev Containers: Attach to Running Container'"
echo "   - Select 'wfc-devcontainer'"
echo ""
echo "4. Firewall mode: $FIREWALL_MODE"
if [[ "$FIREWALL_MODE" == "audit" ]]; then
    echo "   View traffic: sudo tail -f /var/log/kern.log | grep FW-AUDIT"
fi
echo ""
echo "5. WFC Skills available inside container:"
echo "   /wfc-build     - Build features"
echo "   /wfc-review    - Multi-agent consensus review"
echo "   /wfc-plan      - Structured planning"
echo "   /wfc-security  - STRIDE threat modeling"
echo ""
echo -e "${BLUE}World Fucking Class.${NC}"
echo ""
