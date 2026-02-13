#!/usr/bin/env bash
#
# Input validation functions
# Provides validation for user inputs
#

# Validate Anthropic API key format
# Args: $1 - API key to validate
# Returns: 0 if valid, 1 if invalid
validate_api_key() {
    local api_key="$1"

    if [[ ! "$api_key" =~ ^sk-ant- ]]; then
        echo -e "${RED}✗ Invalid API key format${NC}"
        echo -e "${YELLOW}  API keys should start with 'sk-ant-'${NC}"
        echo -e "${YELLOW}  Get a valid key from: https://console.anthropic.com/settings/keys${NC}"
        return 1
    fi

    echo -e "${GREEN}✓ API key format valid${NC}"
    return 0
}

# Validate email format
# Args: $1 - Email to validate
# Returns: 0 if valid, 1 if invalid
validate_email() {
    local email="$1"

    if [[ "$email" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        echo -e "${YELLOW}  Email format may be invalid${NC}"
        return 1
    fi
}

# Validate directory exists
# Args: $1 - Directory path to validate
# Returns: 0 if exists, 1 if not
validate_directory() {
    local dir_path="$1"

    if [[ -d "$dir_path" ]]; then
        return 0
    else
        echo -e "${RED}✗ Directory not found: $dir_path${NC}"
        return 1
    fi
}

# Prompt user with yes/no question
# Args: $1 - prompt message, $2 - default (Y/N)
# Returns: 0 for yes, 1 for no
prompt_yes_no() {
    local prompt="$1"
    local default="${2:-Y}"
    local response

    if [[ "$default" == "Y" ]]; then
        read -p "$prompt (Y/n): " -n 1 -r response
    else
        read -p "$prompt (y/N): " -n 1 -r response
    fi
    echo ""

    if [[ -z "$response" ]]; then
        [[ "$default" == "Y" ]] && return 0 || return 1
    fi

    [[ $response =~ ^[Yy]$ ]] && return 0 || return 1
}
