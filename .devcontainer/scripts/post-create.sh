#!/usr/bin/env bash
#
# Post-Create Script - Runs after container is created
# Sets up development environment and initializes firewall
#

set -euo pipefail

echo "Setting up WFC DevContainer..."

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# ────────────────────────────────────────────────────────────────────────────────
# Sync WFC Home Defaults (smart merge — managed files updated, user files untouched)
# ────────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}► Syncing WFC home directory defaults...${NC}"

DEFAULTS_DIR="/opt/wfc/home-defaults"
HOME_DIR="/home/wfc"

if [[ -d "$DEFAULTS_DIR" ]]; then
    IMAGE_VERSION=$(cat "$DEFAULTS_DIR/.wfc_version" 2>/dev/null || echo "0.0.0")
    HOME_VERSION=$(cat "$HOME_DIR/.wfc_version" 2>/dev/null || echo "0.0.0")

    if [[ "$IMAGE_VERSION" != "$HOME_VERSION" ]]; then
        echo -e "${BLUE}  Updating WFC-managed files (${HOME_VERSION} → ${IMAGE_VERSION})...${NC}"
    else
        echo -e "${GREEN}✓ WFC home defaults up to date (v${IMAGE_VERSION})${NC}"
    fi

    # MANAGED files — always overwrite from image (these are WFC's, not the user's)
    for managed_file in .wfc_env .wfc_motd.sh .healthcheck.sh; do
        if [[ -f "$DEFAULTS_DIR/$managed_file" ]]; then
            cp "$DEFAULTS_DIR/$managed_file" "$HOME_DIR/$managed_file"
            chmod +x "$HOME_DIR/$managed_file" 2>/dev/null || true
        fi
    done

    # SEEDED files — ensure WFC source lines exist without overwriting user content
    for rc_file in .bashrc .zshrc; do
        target="$HOME_DIR/$rc_file"
        # Create if missing (e.g., fresh volume without Docker auto-population)
        touch "$target"
        # Ensure our source lines are present
        grep -qF 'source ~/.wfc_env' "$target" 2>/dev/null || \
            echo 'source ~/.wfc_env' >> "$target"
        grep -qF 'source ~/.wfc_motd.sh' "$target" 2>/dev/null || \
            echo 'source ~/.wfc_motd.sh' >> "$target"
    done

    # Stamp the version so we skip no-op syncs on next restart
    echo "$IMAGE_VERSION" > "$HOME_DIR/.wfc_version"

    echo -e "${GREEN}✓ WFC-managed files synced (v${IMAGE_VERSION})${NC}"
else
    echo -e "${YELLOW}⚠ /opt/wfc/home-defaults not found — skipping sync${NC}"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Initialize Firewall (CRITICAL - Security Boundary)
# ────────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}► Initializing firewall (audit mode by default)...${NC}"

# Initialize firewall with current mode (defaults to audit from .env)
if [[ -f /workspace/app/.devcontainer/scripts/init-firewall.sh ]]; then
    sudo bash /workspace/app/.devcontainer/scripts/init-firewall.sh || {
        echo -e "${RED}✗ Firewall initialization failed${NC}"
        echo -e "${YELLOW}⚠ Running without firewall - not recommended!${NC}"
    }
else
    echo -e "${YELLOW}⚠ Firewall script not found${NC}"
    echo -e "${YELLOW}  Container is running without network restrictions!${NC}"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Verify Essential Tools
# ────────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}► Verifying essential tools...${NC}"

TOOLS_OK=true

# Check Python
if command -v python3 &> /dev/null; then
    echo -e "${GREEN}✓ Python $(python3 --version | cut -d' ' -f2)${NC}"
else
    echo -e "${RED}✗ Python not found${NC}"
    TOOLS_OK=false
fi

# Check Node.js
if command -v node &> /dev/null; then
    echo -e "${GREEN}✓ Node.js $(node --version)${NC}"
else
    echo -e "${RED}✗ Node.js not found${NC}"
    TOOLS_OK=false
fi

# Check UV
if command -v uv &> /dev/null; then
    echo -e "${GREEN}✓ UV (fast Python package manager)${NC}"
else
    echo -e "${YELLOW}⚠ UV not found (falling back to pip)${NC}"
fi

# Check Claude Code
if command -v claude &> /dev/null; then
    echo -e "${GREEN}✓ Claude Code CLI${NC}"
else
    echo -e "${YELLOW}⚠ Claude Code CLI not in PATH${NC}"
fi

# Check GitHub CLI
if command -v gh &> /dev/null; then
    echo -e "${GREEN}✓ GitHub CLI $(gh --version | head -1 | cut -d' ' -f3)${NC}"
else
    echo -e "${YELLOW}⚠ GitHub CLI not available${NC}"
fi

# Check Kiro CLI
if command -v kiro &> /dev/null; then
    echo -e "${GREEN}✓ Kiro CLI${NC}"
else
    echo -e "${YELLOW}⚠ Kiro CLI not available${NC}"
fi

# Check OpenCode CLI
if command -v opencode &> /dev/null; then
    echo -e "${GREEN}✓ OpenCode CLI${NC}"
else
    echo -e "${YELLOW}⚠ OpenCode CLI not available${NC}"
fi

# Check Entire CLI
if command -v entire &> /dev/null; then
    echo -e "${GREEN}✓ Entire CLI (session recording)${NC}"
else
    echo -e "${YELLOW}⚠ Entire CLI not available${NC}"
fi

# Check Docker
if command -v docker &> /dev/null; then
    echo -e "${GREEN}✓ Docker $(docker --version | cut -d' ' -f3 | tr -d ',')${NC}"
else
    echo -e "${YELLOW}⚠ Docker not available${NC}"
fi

# Check Git
if command -v git &> /dev/null; then
    echo -e "${GREEN}✓ Git $(git --version | cut -d' ' -f3)${NC}"
else
    echo -e "${RED}✗ Git not found${NC}"
    TOOLS_OK=false
fi

# ────────────────────────────────────────────────────────────────────────────────
# Setup SSH for Git operations (persistent volume at ~/.ssh)
# ────────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}► Configuring SSH for Git...${NC}"

# Ensure SSH directory has correct permissions (volume may be fresh)
mkdir -p ~/.ssh && chmod 700 ~/.ssh

# Write SSH config if it doesn't exist yet (first run on fresh volume)
if [[ ! -f ~/.ssh/config ]]; then
    cat > ~/.ssh/config <<'SSHEOF'
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519
    IdentityFile ~/.ssh/id_rsa
    ForwardAgent yes
    StrictHostKeyChecking accept-new

Host *
    ForwardAgent yes
    AddKeysToAgent yes
SSHEOF
    chmod 600 ~/.ssh/config
    echo -e "${GREEN}✓ SSH config created${NC}"
else
    echo -e "${GREEN}✓ SSH config exists (persistent volume)${NC}"
fi

# Check if SSH agent forwarding is working
SSH_AGENT_OK=false
if ssh-add -l &>/dev/null; then
    echo -e "${GREEN}✓ SSH agent forwarding is working${NC}"
    ssh-add -l | head -3
    SSH_AGENT_OK=true
else
    echo -e "${YELLOW}⚠ SSH agent forwarding not available${NC}"
fi

# Fallback: generate container-local SSH keypair if none exists and agent isn't forwarded
if [[ "$SSH_AGENT_OK" != "true" ]] && [[ ! -f ~/.ssh/id_ed25519 ]]; then
    echo -e "${BLUE}  Generating container SSH keypair (ed25519)...${NC}"
    ssh-keygen -t ed25519 -C "wfc-devcontainer" -f ~/.ssh/id_ed25519 -N "" -q
    echo -e "${GREEN}✓ SSH keypair generated${NC}"
    echo ""
    echo -e "${YELLOW}  ┌─────────────────────────────────────────────────────────────┐${NC}"
    echo -e "${YELLOW}  │  Add this public key to GitHub:                             │${NC}"
    echo -e "${YELLOW}  │  https://github.com/settings/ssh/new                        │${NC}"
    echo -e "${YELLOW}  └─────────────────────────────────────────────────────────────┘${NC}"
    echo ""
    echo -e "${BLUE}  Public key:${NC}"
    cat ~/.ssh/id_ed25519.pub
    echo ""
    echo -e "${YELLOW}  Or use: gh ssh-key add ~/.ssh/id_ed25519.pub --title wfc-devcontainer${NC}"
    echo ""
elif [[ -f ~/.ssh/id_ed25519 ]]; then
    echo -e "${GREEN}✓ SSH keypair exists (persistent volume)${NC}"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Setup GitHub CLI Authentication (persistent volume at ~/.config/gh)
# ────────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}► Checking GitHub CLI authentication...${NC}"

if command -v gh &> /dev/null; then
    if gh auth status &>/dev/null; then
        echo -e "${GREEN}✓ GitHub CLI authenticated (persistent volume)${NC}"
        gh auth status 2>&1 | head -3
    else
        echo -e "${YELLOW}⚠ GitHub CLI not authenticated${NC}"
        echo -e "${YELLOW}  WFC PR workflow requires gh auth. Run:${NC}"
        echo -e "${BLUE}    gh auth login${NC}"
        echo ""
        echo -e "${YELLOW}  Or authenticate with a token:${NC}"
        echo -e "${BLUE}    echo \$GITHUB_TOKEN | gh auth login --with-token${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}⚠ GitHub CLI not installed — WFC PR workflow unavailable${NC}"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Check WFC Framework
# ────────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}► Checking WFC framework...${NC}"

if [[ -d /workspace/repos/wfc ]]; then
    echo -e "${GREEN}✓ WFC framework found at /workspace/repos/wfc/${NC}"

    # Install WFC if install script exists
    if [[ -f /workspace/repos/wfc/install-universal.sh ]]; then
        echo -e "${BLUE}  Installing WFC skills...${NC}"
        bash /workspace/repos/wfc/install-universal.sh --ci || {
            echo -e "${YELLOW}⚠ WFC install-universal.sh failed${NC}"
        }
    else
        echo -e "${YELLOW}  install-universal.sh not found, skipping WFC skill install${NC}"
    fi
else
    echo -e "${YELLOW}⚠ WFC framework not found${NC}"
    echo -e "${YELLOW}  Clone manually: git clone https://github.com/sam-fakhreddine/wfc.git /workspace/repos/wfc${NC}"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Enable Entire.io Session Recording
# ────────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}► Setting up Entire.io session recording...${NC}"

if command -v entire &> /dev/null; then
    # Enable Entire in the workspace with manual-commit strategy
    if [[ -d /workspace/app/.git ]]; then
        cd /workspace/app
        entire enable --strategy=manual-commit 2>/dev/null && \
            echo -e "${GREEN}✓ Entire.io enabled in /workspace/app${NC}" || \
            echo -e "${YELLOW}⚠ Entire.io enable failed (can run manually: entire enable)${NC}"

        # Set up Claude Code hooks for session capture
        entire hooks claude-code session-start 2>/dev/null && \
            echo -e "${GREEN}✓ Entire.io Claude Code hooks configured${NC}" || \
            echo -e "${YELLOW}⚠ Entire.io hooks setup skipped (run: entire hooks claude-code session-start)${NC}"
        cd /workspace
    else
        echo -e "${YELLOW}⚠ No git repo at /workspace/app — Entire will auto-enable when you init a repo${NC}"
    fi
else
    echo -e "${YELLOW}⚠ Entire CLI not available — session recording disabled${NC}"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Install Pre-commit Hooks
# ────────────────────────────────────────────────────────────────────────────────
echo -e "${BLUE}► Setting up pre-commit hooks...${NC}"

if command -v pre-commit &> /dev/null; then
    if [[ -f /workspace/app/.pre-commit-config.yaml ]]; then
        cd /workspace/app
        pre-commit install 2>/dev/null && \
            echo -e "${GREEN}✓ Pre-commit hooks installed${NC}" || \
            echo -e "${YELLOW}⚠ Pre-commit install failed${NC}"
        cd /workspace
    else
        echo -e "${YELLOW}  No .pre-commit-config.yaml found (skipping)${NC}"
    fi
else
    echo -e "${YELLOW}⚠ pre-commit not available${NC}"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Display Setup Summary
# ────────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║              WFC DevContainer Ready                          ║${NC}"
echo -e "${GREEN}╠═══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${GREEN}║  Environment:                                                ║${NC}"
echo -e "${GREEN}║    Python:     $(python3 --version 2>/dev/null | cut -d' ' -f2 || echo 'N/A')                                       ║${NC}"
echo -e "${GREEN}║    Node.js:    $(node --version 2>/dev/null || echo 'N/A')                                      ║${NC}"
echo -e "${GREEN}║    Claude:     $(command -v claude &>/dev/null && echo 'Installed' || echo 'Not found')                                  ║${NC}"
echo -e "${GREEN}║    GitHub CLI: $(command -v gh &>/dev/null && echo 'Installed' || echo 'Not found')                                  ║${NC}"
echo -e "${GREEN}║    Kiro:       $(command -v kiro &>/dev/null && echo 'Installed' || echo 'Not found')                                  ║${NC}"
echo -e "${GREEN}║    OpenCode:   $(command -v opencode &>/dev/null && echo 'Installed' || echo 'Not found')                                  ║${NC}"
echo -e "${GREEN}║    Entire:     $(command -v entire &>/dev/null && echo 'Installed' || echo 'Not found')                                  ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║  Workspace:                                                  ║${NC}"
echo -e "${GREEN}║    /workspace/app/      - Your application code              ║${NC}"
echo -e "${GREEN}║    /workspace/repos/    - Additional repositories (WFC)      ║${NC}"
echo -e "${GREEN}║    /workspace/tmp/      - Temporary files (persistent)       ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║  Security:                                                   ║${NC}"
echo -e "${GREEN}║    Firewall Mode: ${FIREWALL_MODE:-audit}                                    ║${NC}"
echo -e "${GREEN}║    Full capabilities inside container                        ║${NC}"
echo -e "${GREEN}║    Network-level containment (firewall boundary)             ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║  WFC Skills:                                                 ║${NC}"
echo -e "${GREEN}║    /wfc-build     - Build features (intentional vibe)        ║${NC}"
echo -e "${GREEN}║    /wfc-review    - Multi-agent consensus review             ║${NC}"
echo -e "${GREEN}║    /wfc-plan      - Structured planning                      ║${NC}"
echo -e "${GREEN}║    /wfc-security  - STRIDE threat modeling                   ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║  Next Steps:                                                 ║${NC}"
echo -e "${GREEN}║    1. Your code is in /workspace/app/                        ║${NC}"
echo -e "${GREEN}║    2. Install packages: uv pip install <package>             ║${NC}"
echo -e "${GREEN}║    3. Run Claude Code: claude                                ║${NC}"
echo -e "${GREEN}║    4. Check firewall: sudo tail -f /var/log/kern.log         ║${NC}"
echo -e "${GREEN}║                                                              ║${NC}"
echo -e "${GREEN}║  World Fucking Class.                                        ║${NC}"
echo -e "${GREEN}╚═══════════════════════════════════════════════════════════════╝${NC}"

if [[ "$TOOLS_OK" != "true" ]]; then
    echo ""
    echo -e "${YELLOW}⚠ Some essential tools are missing - check errors above${NC}"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Run Container Verification Suite
# ────────────────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BLUE}► Running container verification suite...${NC}"
echo ""

VERIFY_SCRIPT="/workspace/app/.devcontainer/scripts/verify-container.sh"
if [[ -f "$VERIFY_SCRIPT" ]]; then
    bash "$VERIFY_SCRIPT" || {
        echo -e "${RED}✗ Container verification found failures — check output above${NC}"
    }
else
    echo -e "${YELLOW}⚠ verify-container.sh not found — skipping verification${NC}"
fi

echo ""
