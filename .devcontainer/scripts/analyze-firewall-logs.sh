#!/usr/bin/env bash
#
# Analyze firewall audit logs to see what was accessed
# Generates a summary and suggests whitelist entries
#

set -euo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo "Analyzing firewall audit logs..."
echo ""

# Check if running with sudo
if [[ $EUID -ne 0 ]] && [[ ! -r /var/log/kern.log ]]; then
    echo "Note: May need sudo to read /var/log/kern.log"
    echo "Run: sudo bash $0"
    echo ""
fi

LOG_FILE="/var/log/kern.log"

if [[ ! -f "$LOG_FILE" ]]; then
    echo "Error: $LOG_FILE not found"
    exit 1
fi

# Extract unique destination IPs and ports from audit logs
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  HTTPS Traffic (port 443)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

HTTPS_DESTS=$(grep "FW-AUDIT.*HTTPS" "$LOG_FILE" 2>/dev/null | \
    grep -oP 'DST=\K[0-9.]+' | \
    sort | uniq -c | sort -rn || true)

if [[ -n "$HTTPS_DESTS" ]]; then
    echo "Destination IPs accessed (with counts):"
    echo "$HTTPS_DESTS" | head -20
    echo ""

    # Try to reverse DNS lookup the IPs
    echo "Attempting reverse DNS lookup..."
    echo ""
    while read -r count ip; do
        hostname=$(dig +short -x "$ip" 2>/dev/null | head -1 || echo "unknown")
        printf "  %3d connections → %-15s (%s)\n" "$count" "$ip" "$hostname"
    done <<< "$HTTPS_DESTS" | head -20
else
    echo "No HTTPS traffic logged yet."
    echo "Make sure:"
    echo "  1. Firewall is in audit mode (FIREWALL_MODE=audit)"
    echo "  2. You've used the container to do some work"
    echo "  3. Kernel logging is enabled"
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  HTTP Traffic (port 80)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

HTTP_DESTS=$(grep "FW-AUDIT.*HTTP:" "$LOG_FILE" 2>/dev/null | \
    grep "DPT=80 " | \
    grep -oP 'DST=\K[0-9.]+' | \
    sort | uniq -c | sort -rn || true)

if [[ -n "$HTTP_DESTS" ]]; then
    echo "Destination IPs accessed (with counts):"
    echo "$HTTP_DESTS" | head -20
else
    echo "No HTTP traffic logged (most traffic uses HTTPS)."
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  SSH Traffic (port 22)${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

SSH_DESTS=$(grep "FW-AUDIT.*SSH" "$LOG_FILE" 2>/dev/null | \
    grep -oP 'DST=\K[0-9.]+' | \
    sort | uniq -c | sort -rn || true)

if [[ -n "$SSH_DESTS" ]]; then
    echo "Destination IPs accessed (with counts):"
    echo "$SSH_DESTS"
else
    echo "No SSH traffic logged."
fi

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  DNS Queries${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
echo ""

DNS_DESTS=$(grep "FW-AUDIT.*DNS" "$LOG_FILE" 2>/dev/null | \
    grep -oP 'DST=\K[0-9.]+' | \
    sort | uniq -c | sort -rn || true)

if [[ -n "$DNS_DESTS" ]]; then
    echo "DNS servers queried:"
    echo "$DNS_DESTS"
else
    echo "No DNS traffic logged."
fi

echo ""
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo -e "${YELLOW}  Suggested Whitelist Entries${NC}"
echo -e "${YELLOW}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "Based on the traffic observed, consider adding these to"
echo "init-firewall.sh in enforce mode:"
echo ""

# Generate suggested iptables rules (grouped by likely service)
if [[ -n "$HTTPS_DESTS" ]]; then
    echo "# Add these IP ranges or domains to whitelist:"
    while read -r count ip; do
        hostname=$(dig +short -x "$ip" 2>/dev/null | head -1 || echo "")
        if [[ -n "$hostname" ]]; then
            # Extract base domain
            domain=$(echo "$hostname" | awk -F. '{print $(NF-1)"."$NF}')
            echo "# $count connections to $ip ($hostname)"
            echo "iptables -A OUTPUT -p tcp -d $domain --dport 443 -j ACCEPT"
        else
            echo "# $count connections to $ip (unknown hostname)"
            echo "iptables -A OUTPUT -p tcp -d $ip --dport 443 -j ACCEPT"
        fi
        echo ""
    done <<< "$HTTPS_DESTS" | head -10
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo -e "${BLUE}  Next Steps${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════════════${NC}"
echo ""
echo "1. Review the traffic above"
echo "2. Add necessary domains to whitelist in init-firewall.sh"
echo "3. Test in enforce mode:"
echo "   sudo FIREWALL_MODE=enforce bash /workspace/app/.devcontainer/scripts/init-firewall.sh"
echo "4. Monitor for blocked traffic:"
echo "   sudo tail -f /var/log/kern.log | grep FW-BLOCK"
echo ""

# Offer to generate a whitelist file
echo -e "${YELLOW}Generate whitelist configuration? (y/n)${NC}"
read -r -n 1 response
echo ""

if [[ "$response" =~ ^[Yy]$ ]]; then
    WHITELIST_FILE="/tmp/firewall-whitelist-$(date +%Y%m%d-%H%M%S).sh"

    echo "# Generated firewall whitelist from audit logs" > "$WHITELIST_FILE"
    echo "# Generated at $(date)" >> "$WHITELIST_FILE"
    echo "" >> "$WHITELIST_FILE"

    if [[ -n "$HTTPS_DESTS" ]]; then
        while read -r count ip; do
            hostname=$(dig +short -x "$ip" 2>/dev/null | head -1 || echo "")
            if [[ -n "$hostname" ]]; then
                domain=$(echo "$hostname" | awk -F. '{print $(NF-1)"."$NF}')
                echo "iptables -A OUTPUT -p tcp -d $domain --dport 443 -j ACCEPT  # $count connections" >> "$WHITELIST_FILE"
            fi
        done <<< "$HTTPS_DESTS"
    fi

    echo ""
    echo -e "${GREEN}✓ Whitelist saved to: $WHITELIST_FILE${NC}"
    echo ""
    echo "Review and add entries to init-firewall.sh as needed."
fi
