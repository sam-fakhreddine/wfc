#!/usr/bin/env bash
set -euo pipefail

# ============================================================================
# WFC Universal Installer — Test Suite
# Run: bash scripts/install_test.sh
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_SCRIPT="$REPO_DIR/install-universal.sh"

# ============================================================================
# Test state
# ============================================================================
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0
FAILURES=""

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ============================================================================
# Test helpers
# ============================================================================
setup() {
    TEST_TMPDIR="$(mktemp -d)"
    export HOME="$TEST_TMPDIR/home"
    mkdir -p "$HOME"
}

teardown() {
    rm -rf "$TEST_TMPDIR"
}

assert_eq() {
    local expected="$1"
    local actual="$2"
    local msg="${3:-}"
    if [ "$expected" != "$actual" ]; then
        echo -e "    ${RED}FAIL${NC}: expected '$expected', got '$actual' ${msg}"
        return 1
    fi
}

assert_file_exists() {
    local path="$1"
    local msg="${2:-}"
    if [ ! -f "$path" ]; then
        echo -e "    ${RED}FAIL${NC}: file not found: $path ${msg}"
        return 1
    fi
}

assert_dir_exists() {
    local path="$1"
    local msg="${2:-}"
    if [ ! -d "$path" ]; then
        echo -e "    ${RED}FAIL${NC}: directory not found: $path ${msg}"
        return 1
    fi
}

assert_file_not_empty() {
    local path="$1"
    if [ ! -s "$path" ]; then
        echo -e "    ${RED}FAIL${NC}: file is empty: $path"
        return 1
    fi
}

assert_output_contains() {
    local output="$1"
    local expected="$2"
    local msg="${3:-}"
    if ! echo "$output" | grep -qF -- "$expected"; then
        echo -e "    ${RED}FAIL${NC}: output does not contain '$expected' ${msg}"
        return 1
    fi
}

count_wfc_skills() {
    local dir="$1"
    find "$dir" -maxdepth 1 -type d -name "wfc-*" 2>/dev/null | wc -l | tr -d ' '
}

# Expected skill count from source
EXPECTED_SKILL_COUNT=$(find "$REPO_DIR/wfc/skills" -maxdepth 1 -type d -name "wfc-*" | wc -l | tr -d ' ')

run_test() {
    local test_name="$1"
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "  ${CYAN}TEST${NC}: $test_name"
    if "$@"; then
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "  ${GREEN}PASS${NC}: $test_name"
    else
        TESTS_FAILED=$((TESTS_FAILED + 1))
        FAILURES="${FAILURES}\n  - ${test_name}"
        echo -e "  ${RED}FAIL${NC}: $test_name"
    fi
}

# ============================================================================
# Tests: Help & argument parsing
# ============================================================================

test_help_flag() {
    local output
    output=$(bash "$INSTALL_SCRIPT" --help 2>&1) || true
    assert_output_contains "$output" "USAGE" &&
    assert_output_contains "$output" "--agent" &&
    assert_output_contains "$output" "claude"
}

test_help_short_flag() {
    local output
    output=$(bash "$INSTALL_SCRIPT" -h 2>&1) || true
    assert_output_contains "$output" "USAGE"
}

test_unknown_option() {
    local output
    output=$(bash "$INSTALL_SCRIPT" --bogus 2>&1) || true
    assert_output_contains "$output" "Unknown option"
}

# ============================================================================
# Tests: Source validation
# ============================================================================

test_source_validation_passes() {
    setup
    # Create a fake ~/.claude so platform detection works
    mkdir -p "$HOME/.claude"
    local output
    output=$(bash "$INSTALL_SCRIPT" --agent claude --nsfw 2>&1 </dev/null) || true
    assert_output_contains "$output" "Source validated"
    teardown
}

test_source_validation_counts_skills() {
    setup
    mkdir -p "$HOME/.claude"
    local output
    output=$(bash "$INSTALL_SCRIPT" --agent claude --nsfw 2>&1 </dev/null) || true
    assert_output_contains "$output" "$EXPECTED_SKILL_COUNT skills found"
    teardown
}

# ============================================================================
# Tests: --agent flag installations
# ============================================================================

test_agent_claude() {
    setup
    mkdir -p "$HOME/.claude"
    bash "$INSTALL_SCRIPT" --agent claude --nsfw </dev/null >/dev/null 2>&1 || true
    local count
    count=$(count_wfc_skills "$HOME/.claude/skills")
    assert_eq "$EXPECTED_SKILL_COUNT" "$count" "(claude skills count)"
    teardown
}

test_agent_kiro() {
    setup
    mkdir -p "$HOME/.kiro"
    bash "$INSTALL_SCRIPT" --agent kiro --nsfw </dev/null >/dev/null 2>&1 || true
    local count
    count=$(count_wfc_skills "$HOME/.kiro/skills")
    assert_eq "$EXPECTED_SKILL_COUNT" "$count" "(kiro skills count)"
    teardown
}

test_agent_cursor() {
    setup
    mkdir -p "$HOME/.cursor"
    bash "$INSTALL_SCRIPT" --agent cursor --nsfw </dev/null >/dev/null 2>&1 || true
    local count
    count=$(count_wfc_skills "$HOME/.cursor/skills")
    assert_eq "$EXPECTED_SKILL_COUNT" "$count" "(cursor skills count)"
    teardown
}

test_agent_goose() {
    setup
    mkdir -p "$HOME/.config/goose"
    bash "$INSTALL_SCRIPT" --agent goose --nsfw </dev/null >/dev/null 2>&1 || true
    local count
    count=$(count_wfc_skills "$HOME/.config/goose/skills")
    assert_eq "$EXPECTED_SKILL_COUNT" "$count" "(goose skills count)"
    teardown
}

test_agent_invalid() {
    setup
    local output
    output=$(bash "$INSTALL_SCRIPT" --agent nonexistent --nsfw 2>&1 </dev/null) || true
    assert_output_contains "$output" "Unknown agent"
    teardown
}

# ============================================================================
# Tests: Skill content integrity
# ============================================================================

test_skill_md_exists_in_each() {
    setup
    mkdir -p "$HOME/.claude"
    bash "$INSTALL_SCRIPT" --agent claude --nsfw </dev/null >/dev/null 2>&1 || true
    local missing=0
    for skill_dir in "$HOME/.claude/skills"/wfc-*/; do
        [ -d "$skill_dir" ] || continue
        if [ ! -f "$skill_dir/SKILL.md" ]; then
            echo "    Missing SKILL.md in $(basename "$skill_dir")"
            missing=$((missing + 1))
        fi
    done
    assert_eq "0" "$missing" "(skills missing SKILL.md)"
    teardown
}

test_skill_md_not_empty() {
    setup
    mkdir -p "$HOME/.claude"
    bash "$INSTALL_SCRIPT" --agent claude --nsfw </dev/null >/dev/null 2>&1 || true
    local empty=0
    for skill_md in "$HOME/.claude/skills"/wfc-*/SKILL.md; do
        [ -f "$skill_md" ] || continue
        if [ ! -s "$skill_md" ]; then
            echo "    Empty SKILL.md: $skill_md"
            empty=$((empty + 1))
        fi
    done
    assert_eq "0" "$empty" "(empty SKILL.md files)"
    teardown
}

test_content_matches_source() {
    setup
    mkdir -p "$HOME/.claude"
    bash "$INSTALL_SCRIPT" --agent claude --nsfw </dev/null >/dev/null 2>&1 || true
    local mismatches=0
    for source_skill in "$REPO_DIR/wfc/skills"/wfc-*/SKILL.md; do
        [ -f "$source_skill" ] || continue
        local skill_name
        skill_name=$(basename "$(dirname "$source_skill")")
        local installed="$HOME/.claude/skills/$skill_name/SKILL.md"
        if [ -f "$installed" ]; then
            if ! diff -q "$source_skill" "$installed" >/dev/null 2>&1; then
                echo "    Content mismatch: $skill_name/SKILL.md"
                mismatches=$((mismatches + 1))
            fi
        fi
    done
    assert_eq "0" "$mismatches" "(content mismatches)"
    teardown
}

# ============================================================================
# Tests: Idempotency
# ============================================================================

test_idempotent_install() {
    setup
    mkdir -p "$HOME/.claude"
    # First install
    bash "$INSTALL_SCRIPT" --agent claude --nsfw </dev/null >/dev/null 2>&1 || true
    local count1
    count1=$(count_wfc_skills "$HOME/.claude/skills")

    # Second install
    bash "$INSTALL_SCRIPT" --agent claude --nsfw </dev/null >/dev/null 2>&1 || true
    local count2
    count2=$(count_wfc_skills "$HOME/.claude/skills")

    assert_eq "$count1" "$count2" "(idempotent skill count)"
    teardown
}

# ============================================================================
# Tests: Branding flags
# ============================================================================

test_sfw_branding() {
    setup
    mkdir -p "$HOME/.claude"
    bash "$INSTALL_SCRIPT" --agent claude --sfw </dev/null >/dev/null 2>&1 || true
    # Check branding file exists in either location
    local branding_file=""
    if [ -f "$HOME/.wfc/.wfc_branding" ]; then
        branding_file="$HOME/.wfc/.wfc_branding"
    elif [ -f "$HOME/.claude/skills/.wfc_branding" ]; then
        branding_file="$HOME/.claude/skills/.wfc_branding"
    fi
    if [ -n "$branding_file" ]; then
        local mode
        mode=$(grep "^mode=" "$branding_file" | cut -d'=' -f2)
        assert_eq "sfw" "$mode" "(branding mode)"
    fi
    # At minimum, skills should be installed
    local count
    count=$(count_wfc_skills "$HOME/.claude/skills")
    [ "$count" -gt 0 ]
    teardown
}

test_nsfw_branding() {
    setup
    mkdir -p "$HOME/.claude"
    bash "$INSTALL_SCRIPT" --agent claude --nsfw </dev/null >/dev/null 2>&1 || true
    local branding_file=""
    if [ -f "$HOME/.wfc/.wfc_branding" ]; then
        branding_file="$HOME/.wfc/.wfc_branding"
    elif [ -f "$HOME/.claude/skills/.wfc_branding" ]; then
        branding_file="$HOME/.claude/skills/.wfc_branding"
    fi
    if [ -n "$branding_file" ]; then
        local mode
        mode=$(grep "^mode=" "$branding_file" | cut -d'=' -f2)
        assert_eq "nsfw" "$mode" "(branding mode)"
    fi
    local count
    count=$(count_wfc_skills "$HOME/.claude/skills")
    [ "$count" -gt 0 ]
    teardown
}

# ============================================================================
# Tests: Output messages
# ============================================================================

test_output_shows_installation_complete() {
    setup
    mkdir -p "$HOME/.claude"
    local output
    output=$(bash "$INSTALL_SCRIPT" --agent claude --nsfw 2>&1 </dev/null) || true
    assert_output_contains "$output" "Installation Complete"
    teardown
}

test_output_shows_key_skills() {
    setup
    mkdir -p "$HOME/.claude"
    local output
    output=$(bash "$INSTALL_SCRIPT" --agent claude --nsfw 2>&1 </dev/null) || true
    assert_output_contains "$output" "/wfc-review" &&
    assert_output_contains "$output" "/wfc-build" &&
    assert_output_contains "$output" "/wfc-plan"
    teardown
}

test_output_shows_next_steps() {
    setup
    mkdir -p "$HOME/.claude"
    local output
    output=$(bash "$INSTALL_SCRIPT" --agent claude --nsfw 2>&1 </dev/null) || true
    assert_output_contains "$output" "Next Steps" &&
    assert_output_contains "$output" "Claude Code"
    teardown
}

# ============================================================================
# Tests: Platform auto-creation with --agent
# ============================================================================

test_agent_creates_missing_platform() {
    setup
    # Don't create ~/.claude — the --agent flag should handle it
    bash "$INSTALL_SCRIPT" --agent claude --nsfw </dev/null >/dev/null 2>&1 || true
    local count
    count=$(count_wfc_skills "$HOME/.claude/skills")
    [ "$count" -gt 0 ]
    teardown
}

# ============================================================================
# Run all tests
# ============================================================================

echo ""
echo -e "${BOLD}${CYAN}WFC Installer Test Suite${NC}"
echo -e "${BOLD}${CYAN}========================${NC}"
echo -e "  Source: $INSTALL_SCRIPT"
echo -e "  Expected skills: $EXPECTED_SKILL_COUNT"
echo ""

run_test test_help_flag
run_test test_help_short_flag
run_test test_unknown_option
run_test test_source_validation_passes
run_test test_source_validation_counts_skills
run_test test_agent_claude
run_test test_agent_kiro
run_test test_agent_cursor
run_test test_agent_goose
run_test test_agent_invalid
run_test test_skill_md_exists_in_each
run_test test_skill_md_not_empty
run_test test_content_matches_source
run_test test_idempotent_install
run_test test_sfw_branding
run_test test_nsfw_branding
run_test test_output_shows_installation_complete
run_test test_output_shows_key_skills
run_test test_output_shows_next_steps
run_test test_agent_creates_missing_platform

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${BOLD}Results${NC}"
echo -e "  Total:  $TESTS_RUN"
echo -e "  ${GREEN}Passed: $TESTS_PASSED${NC}"
if [ "$TESTS_FAILED" -gt 0 ]; then
    echo -e "  ${RED}Failed: $TESTS_FAILED${NC}"
    echo -e "\n${RED}Failures:${NC}${FAILURES}"
    echo ""
    exit 1
else
    echo ""
    echo -e "${GREEN}${BOLD}All tests passed.${NC}"
    echo ""
fi
