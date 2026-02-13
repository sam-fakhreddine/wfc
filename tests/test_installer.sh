#!/usr/bin/env bash
# Test Suite for WFC Universal Installer

set -e

TEST_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

pass() {
    echo -e "${GREEN}✓ PASS${RESET}: $1"
    PASS_COUNT=$((PASS_COUNT + 1))
    TEST_COUNT=$((TEST_COUNT + 1))
}

fail() {
    echo -e "${RED}✗ FAIL${RESET}: $1"
    FAIL_COUNT=$((FAIL_COUNT + 1))
    TEST_COUNT=$((TEST_COUNT + 1))
}

cleanup() {
    rm -rf /tmp/wfc-test-*
}

echo "==================================="
echo "WFC Installer Test Suite"
echo "==================================="
echo ""

# Test 1: Installer script is executable
if [ -x "install-universal.sh" ]; then
    pass "install-universal.sh is executable"
else
    fail "install-universal.sh is not executable"
fi

# Test 2: Symlink exists
if [ -L "install.sh" ]; then
    pass "install.sh symlink exists"
    if [ "$(readlink install.sh)" = "install-universal.sh" ]; then
        pass "install.sh points to install-universal.sh"
    else
        fail "install.sh does not point to install-universal.sh"
    fi
else
    fail "install.sh symlink does not exist"
fi

# Test 3: Help flag works
if ./install-universal.sh --help >/dev/null 2>&1; then
    pass "Help flag works (--help)"
else
    fail "Help flag failed"
fi

# Test 4: Version check
VERSION=$(grep "^VERSION=" install-universal.sh | cut -d'"' -f2)
if [ -n "$VERSION" ]; then
    pass "Version defined: $VERSION"
else
    fail "Version not defined"
fi

# Test 5: Skills directory exists
if [ -d "wfc/skills" ]; then
    SKILL_COUNT=$(find wfc/skills -name "SKILL.md" -type f | wc -l)
    pass "Skills directory exists with $SKILL_COUNT skills"

    if [ $SKILL_COUNT -gt 0 ]; then
        pass "Skills have SKILL.md files"

        # Test 6: Check a few skills for valid structure
        VALID_SKILLS=0
        for skill in wfc/skills/wfc-*/; do
            if [ -d "$skill" ] && [ -f "$skill/SKILL.md" ]; then
                VALID_SKILLS=$((VALID_SKILLS + 1))
            fi
        done

        if [ $VALID_SKILLS -gt 0 ]; then
            pass "Valid skill structure: $VALID_SKILLS skills with SKILL.md"
        else
            fail "No valid skills found"
        fi
    else
        fail "No SKILL.md files found"
    fi
else
    fail "Skills directory does not exist"
fi

# Test 7: Personas directory exists
if [ -d "wfc/references/personas" ]; then
    PERSONA_COUNT=$(find wfc/references/personas -name "*.json" -type f | wc -l)
    pass "Personas directory exists with $PERSONA_COUNT personas"
else
    fail "Personas directory does not exist"
fi

# Test 8: CI mode detection in code
if grep -q '\[ "\$CI_MODE" = true \]' install-universal.sh; then
    pass "CI mode logic present"
else
    fail "CI mode logic missing"
fi

# Test 9: Direct mode installs to correct location
if grep -q 'WFC_ROOT="${PLATFORM_PATHS\[$platform\]}"' install-universal.sh; then
    pass "Direct mode installs to platform path directly"
else
    fail "Direct mode path fix missing"
fi

# Test 10: Skills path correction
if grep -q 'wfc/skills"/wfc-\*' install-universal.sh; then
    pass "Skills source path corrected to wfc/skills"
else
    fail "Skills source path still wrong"
fi

echo ""
echo "==================================="
echo "Test Results"
echo "==================================="
echo "Total:  $TEST_COUNT"
echo -e "${GREEN}Passed: $PASS_COUNT${RESET}"
echo -e "${RED}Failed: $FAIL_COUNT${RESET}"

if [ $FAIL_COUNT -eq 0 ]; then
    echo ""
    echo -e "${GREEN}${BOLD}All tests passed!${RESET}"
    exit 0
else
    echo ""
    echo -e "${RED}${BOLD}Some tests failed!${RESET}"
    exit 1
fi
