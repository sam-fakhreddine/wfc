#!/bin/bash

# Multi-flavor Docker test suite for WFC installer
# Tests installation across 5 different Linux distributions

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Configuration
FLAVORS=(
    "ubuntu:24.04"
    "debian:12"
    "fedora:41"
    "alpine:latest"
    "archlinux:base"
)

TEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONTAINER_NAME_PREFIX="wfc-test-"
RESULT_DIR="$TEST_DIR/test-results"
LOG_FILE="$RESULT_DIR/test-suite.log"

# Create results directory
mkdir -p "$RESULT_DIR"

# Initialize results
declare -A RESULTS
declare -A ERROR_MSGS

# Function to log messages
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Function to create Dockerfile for a specific flavor
create_dockerfile() {
    local flavor=$1
    local dockerfile="$RESULT_DIR/Dockerfile.$flavor"

    cat > "$dockerfile" << EOD
# Dockerfile for $flavor
FROM $flavor

# Set working directory
WORKDIR /wfc

# Install basic dependencies and test requirements
EOD

    case $flavor in
        *ubuntu*|*debian*)
            cat >> "$dockerfile" << EOD
# Ubuntu/Debian specific setup
RUN apt-get update && apt-get install -y \
    curl \
    git \
    python3 \
    python3-pip \
    bash \
    && rm -rf /var/lib/apt/lists/*
EOD
            ;;
        *fedora*)
            cat >> "$dockerfile" << EOD
# Fedora specific setup
RUN dnf update -y && dnf install -y \
    curl \
    git \
    python3 \
    python3-pip \
    bash \
    && dnf clean all
EOD
            ;;
        *alpine*)
            cat >> "$dockerfile" << EOD
# Alpine specific setup
RUN apk add --no-cache \
    curl \
    git \
    python3 \
    py3-pip \
    bash \
    && rm -rf /var/cache/apk/*
EOD
            ;;
        *archlinux*)
            cat >> "$dockerfile" << EOD
# Arch Linux specific setup
RUN pacman -Syu --noconfirm \
    curl \
    git \
    python \
    python-pip \
    bash \
    && pacman -Scc --noconfirm
EOD
            ;;
    esac

    cat >> "$dockerfile" << EOD

# Copy WFC source code
COPY . /

# Create Claude Code directory structure
RUN mkdir -p /home/sambou/.claude/skills && \
    mkdir -p /home/sambou/.wfc

# Set environment variables
ENV HOME=/home/sambou

# Create verification script
RUN echo '#!/bin/bash' > /verify.sh && \
    echo 'echo "=== WFC INSTALLATION VERIFICATION ==="' >> /verify.sh && \
    echo 'if [ -d /home/sambou/.claude/skills ]; then' >> /verify.sh && \
    echo '    echo "✅ Skills directory exists"' >> /verify.sh && \
    echo '    SKILL_COUNT=$(find /home/sambou/.claude/skills/ -mindepth 1 -maxdepth 1 -type d | wc -l)' >> /verify.sh && \
    echo '    echo "📊 Skills installed: $SKILL_COUNT"' >> /verify.sh && \
    echo '    echo "📋 Installed skills:"' >> /verify.sh && \
    echo '    find /home/sambou/.claude/skills/ -mindepth 1 -maxdepth 1 -type d -printf "  • %f\\n"' >> /verify.sh && \
    echo '    echo "✅ Installation verification complete"' >> /verify.sh && \
    echo 'else' >> /verify.sh && \
    echo '    echo "❌ Skills directory not found"' >> /verify.sh && \
    echo '    exit 1' >> /verify.sh && \
    echo 'fi' >> /verify.sh && \
    echo 'echo "=== END VERIFICATION ==="' >> /verify.sh && \
    chmod +x /verify.sh

# Run the installer with verification
CMD ["/bin/bash", "-c", "export HOME=/home/sambou && echo '=== Starting WFC Installation ===' && /install-universal.sh --ci && echo '=== Starting Verification ===' && bash /verify.sh"]
EOD
}

# Function to test a specific flavor
test_flavor() {
    local flavor=$1
    local container_name="${CONTAINER_NAME_PREFIX}${flavor//[:.]/-}"
    local dockerfile="$RESULT_DIR/Dockerfile.$flavor"
    local log_file="$RESULT_DIR/${flavor//[:.]/-}.log"

    log "${YELLOW}Testing $flavor...${NC}"
    echo "=== Testing $flavor ===" > "$log_file"

    # Create Dockerfile
    log "  Creating Dockerfile..."
    create_dockerfile "$flavor"

    # Build Docker image
    log "  Building Docker image..."
    if ! docker build -f "$dockerfile" -t "$container_name" . 2>> "$log_file"; then
        RESULTS["$flavor"]="FAIL"
        ERROR_MSGS["$flavor"]="Docker build failed"
        log "${RED}  ❌ Docker build failed for $flavor${NC}"
        return 1
    fi

    # Run container
    log "  Running container..."
    if ! docker run --rm "$container_name" >> "$log_file" 2>&1; then
        RESULTS["$flavor"]="FAIL"
        ERROR_MSGS["$flavor"]="Container execution failed"
        log "${RED}  ❌ Container execution failed for $flavor${NC}"
        return 1
    fi

    # Extract verification results from log
    local skill_count
    skill_count=$(grep -A1 "📊 Skills installed:" "$log_file" | tail -1 | tr -d '\r')

    # Extract skill list from log
    local skill_list
    skill_list=$(grep -A10 "📋 Installed skills:" "$log_file" | tail +2 | sed '/^=== END VERIFICATION ===/,$d')

    RESULTS["$flavor"]="PASS"
    ERROR_MSGS["$flavor"]=""
    log "${GREEN}  ✅ $flavor passed! (Skills installed: ${skill_count:-0})${NC}"

    # Add skill details to log
    echo "=== Skill Details ===" >> "$log_file"
    echo "$skill_list" >> "$log_file" 2>/dev/null || echo "No skills found" >> "$log_file"
}

# Function to generate summary
generate_summary() {
    log "\n${YELLOW}=== TEST SUMMARY ===${NC}"
    log "Total flavors tested: ${#FLAVORS[@]}"

    local pass_count=0
    local fail_count=0

    for flavor in "${FLAVORS[@]}"; do
        if [[ "${RESULTS[$flavor]}" == "PASS" ]]; then
            log "${GREEN}✅ $flavor - PASS${NC}"
            ((pass_count++))
        else
            log "${RED}❌ $flavor - FAIL${NC}"
            if [[ -n "${ERROR_MSGS[$flavor]}" ]]; then
                log "   Error: ${ERROR_MSGS[$flavor]}"
            fi
            ((fail_count++))
        fi
    done

    log "\n${YELLOW}Results:${NC}"
    log "Passed: $pass_count/${#FLAVORS[@]}"
    log "Failed: $fail_count/${#FLAVORS[@]}"

    if [[ $fail_count -eq 0 ]]; then
        log "${GREEN}🎉 All flavors passed!${NC}"
        return 0
    else
        log "${RED}⚠️  Some flavors failed. Check log files for details.${NC}"
        return 1
    fi
}

# Clean up function
cleanup() {
    log "${YELLOW}Cleaning up...${NC}"
    for flavor in "${FLAVORS[@]}"; do
        local container_name="${CONTAINER_NAME_PREFIX}${flavor//[:.]/-}"
        if docker ps -a --format "{{.Names}}" | grep -q "^${container_name}$"; then
            docker rm -f "$container_name" >/dev/null 2>&1 || true
        fi
        if docker images --format "{{.Repository}}:{{.Tag}}" | grep -q "^${container_name}$"; then
            docker rmi "$container_name" >/dev/null 2>&1 || true
        fi
    done
    log "Cleanup complete."
}

# Main test execution
main() {
    log "Starting multi-flavor Docker test suite..."
    log "Test directory: $TEST_DIR"
    log "Results directory: $RESULT_DIR"
    log "Time: $(date)"
    log ""

    # Initialize results
    for flavor in "${FLAVORS[@]}"; do
        RESULTS["$flavor"]=""
        ERROR_MSGS["$flavor"]=""
    done

    # Test each flavor
    for flavor in "${FLAVORS[@]}"; do
        test_flavor "$flavor"
        log ""  # Add spacing between tests
    done

    # Generate summary
    generate_summary

    # Clean up
    cleanup

    # Show individual test logs
    log "\n${YELLOW}Individual test logs:${NC}"
    for flavor in "${FLAVORS[@]}"; do
        local log_file="$RESULT_DIR/${flavor//[:.]/-}.log"
        if [[ -f "$log_file" ]]; then
            log "📄 $log_file"
        fi
    done
}

# Exit handler
trap cleanup EXIT

# Run main function
main "$@"
