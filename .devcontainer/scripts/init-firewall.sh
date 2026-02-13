#!/usr/bin/env bash
#
# WFC DevContainer Firewall Configuration
#
# AUDIT MODE: Logs all connection attempts without blocking
# - Set FIREWALL_MODE=audit to see what gets accessed
# - Set FIREWALL_MODE=enforce to block non-whitelisted traffic
#
# Implements multi-layered security approach with precise access control:
# - Whitelisted outbound connections only (npm registry, GitHub, PyPI, etc.)
# - Allows DNS and SSH connections
# - Default-deny policy for all other external network access
# - Startup verification of firewall rules
#

set -euo pipefail

# ────────────────────────────────────────────────────────────────────────────────
# Configuration
# ────────────────────────────────────────────────────────────────────────────────

# FIREWALL_MODE: "audit" or "enforce"
# - audit:   Log all connections, don't block (see what Claude needs)
# - enforce: Block non-whitelisted connections (production mode)
FIREWALL_MODE="${FIREWALL_MODE:-audit}"

echo "Configuring WFC DevContainer firewall..."
echo "   Mode: ${FIREWALL_MODE}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# ────────────────────────────────────────────────────────────────────────────────
# Check if running as root (required for firewall rules)
# ────────────────────────────────────────────────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}Error: This script must be run as root${NC}"
    echo "Please run with sudo or configure in devcontainer.json with privileged mode"
    exit 1
fi

# ────────────────────────────────────────────────────────────────────────────────
# Install iptables if not present
# ────────────────────────────────────────────────────────────────────────────────
if ! command -v iptables &> /dev/null; then
    echo "Installing iptables..."
    apt-get update
    apt-get install -y iptables
fi

# ────────────────────────────────────────────────────────────────────────────────
# Define firewall policies
# ────────────────────────────────────────────────────────────────────────────────

# Flush existing rules
iptables -F
iptables -X
iptables -Z

if [[ "$FIREWALL_MODE" == "audit" ]]; then
    echo -e "${YELLOW}  AUDIT MODE: Logging all traffic, NOT blocking${NC}"
    # In audit mode: Allow everything, but log it
    iptables -P INPUT ACCEPT
    iptables -P FORWARD DROP
    iptables -P OUTPUT ACCEPT
else
    echo -e "${GREEN}✓ ENFORCE MODE: Blocking non-whitelisted traffic${NC}"
    # In enforce mode: Default deny
    iptables -P INPUT DROP
    iptables -P FORWARD DROP
    iptables -P OUTPUT DROP
fi

# ────────────────────────────────────────────────────────────────────────────────
# Allow loopback traffic (localhost communication)
# ────────────────────────────────────────────────────────────────────────────────
iptables -A INPUT -i lo -j ACCEPT
iptables -A OUTPUT -o lo -j ACCEPT

# ────────────────────────────────────────────────────────────────────────────────
# Allow established and related connections
# ────────────────────────────────────────────────────────────────────────────────
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

if [[ "$FIREWALL_MODE" == "enforce" ]]; then
    iptables -A OUTPUT -m state --state ESTABLISHED,RELATED -j ACCEPT
fi

# ────────────────────────────────────────────────────────────────────────────────
# Allow DNS queries (essential for package management and development)
# ────────────────────────────────────────────────────────────────────────────────
if [[ "$FIREWALL_MODE" == "audit" ]]; then
    iptables -A OUTPUT -p udp --dport 53 -j LOG --log-prefix "[FW-AUDIT] DNS: " --log-level 6
    iptables -A OUTPUT -p tcp --dport 53 -j LOG --log-prefix "[FW-AUDIT] DNS: " --log-level 6
fi
iptables -A OUTPUT -p udp --dport 53 -j ACCEPT
iptables -A OUTPUT -p tcp --dport 53 -j ACCEPT

# ────────────────────────────────────────────────────────────────────────────────
# Allow SSH connections (for Git operations via SSH)
# ────────────────────────────────────────────────────────────────────────────────
if [[ "$FIREWALL_MODE" == "audit" ]]; then
    iptables -A OUTPUT -p tcp --dport 22 -j LOG --log-prefix "[FW-AUDIT] SSH: " --log-level 6
fi
iptables -A OUTPUT -p tcp --dport 22 -j ACCEPT

# ────────────────────────────────────────────────────────────────────────────────
# HTTP/HTTPS Traffic - Log and categorize by destination
# ────────────────────────────────────────────────────────────────────────────────

if [[ "$FIREWALL_MODE" == "audit" ]]; then
    # In audit mode: Log ALL HTTP/HTTPS to see what's accessed
    echo -e "${BLUE}  Audit mode: Logging all HTTP/HTTPS traffic to /var/log/kern.log${NC}"

    # Log HTTP (port 80)
    iptables -A OUTPUT -p tcp --dport 80 -j LOG --log-prefix "[FW-AUDIT] HTTP: " --log-level 6
    iptables -A OUTPUT -p tcp --dport 80 -j ACCEPT

    # Log HTTPS (port 443) - this is where most traffic will be
    iptables -A OUTPUT -p tcp --dport 443 -j LOG --log-prefix "[FW-AUDIT] HTTPS: " --log-level 6
    iptables -A OUTPUT -p tcp --dport 443 -j ACCEPT

else
    # In enforce mode: ONLY allow whitelisted domains
    # NOTE: We do NOT have blanket port 80/443 rules here!
    # Each service must be explicitly whitelisted below

    # PyPI (Python Package Index)
    iptables -A OUTPUT -p tcp -d pypi.org --dport 443 -j ACCEPT
    iptables -A OUTPUT -p tcp -d files.pythonhosted.org --dport 443 -j ACCEPT
    iptables -A OUTPUT -p tcp -d pypi.org --dport 80 -j ACCEPT

    # npm registry
    iptables -A OUTPUT -p tcp -d registry.npmjs.org --dport 443 -j ACCEPT
    iptables -A OUTPUT -p tcp -d www.npmjs.com --dport 443 -j ACCEPT

    # GitHub (for git operations and API access)
    iptables -A OUTPUT -p tcp -d github.com --dport 443 -j ACCEPT
    iptables -A OUTPUT -p tcp -d api.github.com --dport 443 -j ACCEPT
    iptables -A OUTPUT -p tcp -d codeload.github.com --dport 443 -j ACCEPT
    iptables -A OUTPUT -p tcp -d raw.githubusercontent.com --dport 443 -j ACCEPT
    iptables -A OUTPUT -p tcp -d objects.githubusercontent.com --dport 443 -j ACCEPT
    iptables -A OUTPUT -p tcp -d github.com --dport 22 -j ACCEPT  # SSH

    # Claude API (for Claude Code access)
    iptables -A OUTPUT -p tcp -d api.anthropic.com --dport 443 -j ACCEPT

    # Docker Hub (for container images)
    iptables -A OUTPUT -p tcp -d hub.docker.com --dport 443 -j ACCEPT
    iptables -A OUTPUT -p tcp -d registry-1.docker.io --dport 443 -j ACCEPT
    iptables -A OUTPUT -p tcp -d production.cloudflare.docker.com --dport 443 -j ACCEPT
    iptables -A OUTPUT -p tcp -d auth.docker.io --dport 443 -j ACCEPT

    # Add more whitelisted services here as needed
    # Example:
    # iptables -A OUTPUT -p tcp -d example.com --dport 443 -j ACCEPT
fi

# ────────────────────────────────────────────────────────────────────────────────
# Allow local network communication (for Docker Compose services)
# ────────────────────────────────────────────────────────────────────────────────
# Docker network ranges - always allowed
iptables -A INPUT -s 172.16.0.0/12 -j ACCEPT
iptables -A OUTPUT -d 172.16.0.0/12 -j ACCEPT
iptables -A INPUT -s 192.168.0.0/16 -j ACCEPT
iptables -A OUTPUT -d 192.168.0.0/16 -j ACCEPT

# ────────────────────────────────────────────────────────────────────────────────
# Log blocked traffic (enforce mode only)
# ────────────────────────────────────────────────────────────────────────────────
if [[ "$FIREWALL_MODE" == "enforce" ]]; then
    # Log any traffic that would be blocked (for debugging whitelist gaps)
    iptables -A OUTPUT -p tcp --dport 80 -j LOG --log-prefix "[FW-BLOCK] HTTP: " --log-level 4
    iptables -A OUTPUT -p tcp --dport 443 -j LOG --log-prefix "[FW-BLOCK] HTTPS: " --log-level 4
    iptables -A OUTPUT -j LOG --log-prefix "[FW-BLOCK] OTHER: " --log-level 4
fi

# ────────────────────────────────────────────────────────────────────────────────
# Save iptables rules for persistence
# ────────────────────────────────────────────────────────────────────────────────
if command -v iptables-save &> /dev/null; then
    mkdir -p /etc/iptables 2>/dev/null || true
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || \
    iptables-save > /etc/iptables.rules 2>/dev/null || \
    echo "Warning: Could not persist iptables rules"
fi

# ────────────────────────────────────────────────────────────────────────────────
# Verify and display firewall rules
# ────────────────────────────────────────────────────────────────────────────────
echo ""
echo "Firewall rules configured:"
echo ""

# Display active rules
iptables -L -n -v | head -30

echo ""
echo -e "${GREEN}✓ Firewall configuration complete${NC}"
echo ""

if [[ "$FIREWALL_MODE" == "audit" ]]; then
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo -e "${YELLOW}  AUDIT MODE ACTIVE${NC}"
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  All traffic is ALLOWED but LOGGED to:"
    echo "    /var/log/kern.log"
    echo ""
    echo "  View live traffic:"
    echo -e "    ${BLUE}sudo tail -f /var/log/kern.log | grep FW-AUDIT${NC}"
    echo ""
    echo "  Switch to enforce mode:"
    echo -e "    ${BLUE}sudo FIREWALL_MODE=enforce bash /workspace/app/.devcontainer/scripts/init-firewall.sh${NC}"
    echo ""
    echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
else
    echo "Allowed outbound connections:"
    echo "  DNS (port 53)"
    echo "  SSH (port 22)"
    echo "  PyPI (pypi.org, files.pythonhosted.org)"
    echo "  npm registry (registry.npmjs.org)"
    echo "  GitHub (github.com, api.github.com, etc.)"
    echo "  Claude API (api.anthropic.com)"
    echo "  Docker Hub (hub.docker.com, registry-1.docker.io)"
    echo "  Local networks (172.16.0.0/12, 192.168.0.0/16)"
    echo ""
    echo -e "${YELLOW}Note: All other outbound connections are BLOCKED${NC}"
    echo ""
    echo "View blocked connection attempts:"
    echo -e "  ${BLUE}sudo tail -f /var/log/kern.log | grep FW-BLOCK${NC}"
fi
echo ""
