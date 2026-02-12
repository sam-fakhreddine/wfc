#!/usr/bin/env bash
#
# WFC Branding Helper
# Returns branding information based on user's installation choice
#
# Usage:
#   source scripts/get_branding.sh
#   echo "$WFC_NAME"        # "World Fucking Class" or "Workflow Champion"
#   echo "$WFC_MODE"        # "nsfw" or "sfw"
#   echo "$WFC_TAGLINE"     # Full tagline
#

# Check possible branding config locations
BRANDING_PATHS=(
    "$HOME/.wfc/.wfc_branding"
    "$HOME/.claude/skills/wfc/.wfc_branding"
    "$HOME/.kiro/skills/wfc/.wfc_branding"
)

WFC_MODE="nsfw"  # Default
WFC_NAME="World Fucking Class"
WFC_TAGLINE="Multi-Agent Framework That Doesn't Fuck Around"

# Try to load branding config
for path in "${BRANDING_PATHS[@]}"; do
    if [ -f "$path" ]; then
        # Source the config
        source "$path"
        break
    fi
done

# Export for use in other scripts
export WFC_MODE
export WFC_NAME
export WFC_TAGLINE

# Utility function to get branding-aware messages
wfc_message() {
    local key="$1"

    case "$key" in
        tagline)
            if [ "$WFC_MODE" = "sfw" ]; then
                echo "This is Workflow Champion."
            else
                echo "This is World Fucking Class."
            fi
            ;;
        success)
            if [ "$WFC_MODE" = "sfw" ]; then
                echo "Success! Workflow Champion is ready."
            else
                echo "Success! World Fucking Class is ready."
            fi
            ;;
        error)
            if [ "$WFC_MODE" = "sfw" ]; then
                echo "Error: Workflow Champion encountered an issue."
            else
                echo "Error: WFC doesn't tolerate failures."
            fi
            ;;
        *)
            echo "$WFC_NAME"
            ;;
    esac
}

export -f wfc_message
