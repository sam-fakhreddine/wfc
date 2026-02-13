#!/usr/bin/env bash
# Comprehensive WFC Installer Test Suite
# Tests multiple scenarios in Docker

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RESET='\033[0m'

SCENARIO_COUNT=0
PASS_COUNT=0
FAIL_COUNT=0

test_scenario() {
    local name="$1"
    local test_cmd="$2"

    SCENARIO_COUNT=$((SCENARIO_COUNT + 1))

    echo -e "${CYAN}Scenario $SCENARIO_COUNT: ${name}${RESET}"
    echo "──────────────────────────────────────────────"

    # Run command and check exit code
    if bash -c "$test_cmd" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${RESET}\n"
        PASS_COUNT=$((PASS_COUNT + 1))
    else
        echo -e "${RED}✗ FAILED${RESET}\n"
        FAIL_COUNT=$((FAIL_COUNT + 1))
    fi
}

# Scenario 1: Fresh Install (CI Mode)
test_scenario "Fresh Install (CI Mode)" '
docker run --rm wfc-installer-test:latest bash -c "/test.sh" >/dev/null 2>&1
'

# Scenario 2: Skills Load in Claude (verify structure)
test_scenario "Verify Skill Directory Structure" '
docker run --rm wfc-installer-test:latest bash -c "ls /root/.claude/skills/wfc-*/SKILL.md 2>/dev/null | wc -l | grep -q 12"
'

# Scenario 3: No Nested Structure Bug
test_scenario "No Nested wfc/skills/ Directory" '
docker run --rm wfc-installer-test:latest bash -c "[ ! -d /root/.claude/skills/wfc/skills ]"
'

# Scenario 4: Shared Resources
test_scenario "Shared Resources (personas) Installed" '
docker run --rm wfc-installer-test:latest bash -c "[ -d /root/.claude/skills/wfc/personas ]"
'

# Scenario 5: Branding Config
test_scenario "Branding Config Created" '
docker run --rm wfc-installer-test:latest bash -c "[ -f /root/.claude/skills/.wfc_branding ] && grep -q mode=nsfw /root/.claude/skills/.wfc_branding"
'

# Scenario 6: All Skills Have SKILL.md
test_scenario "All Skills Have Valid SKILL.md" '
docker run --rm wfc-installer-test:latest bash -c "find /root/.claude/skills/wfc-*/SKILL.md -type f | wc -l | grep -q 12"
'

# Scenario 7: Skill Names Are Correct
test_scenario "Skill Names Use wfc- Prefix" '
docker run --rm wfc-installer-test:latest bash -c "ls /root/.claude/skills/ | grep wfc- | wc -l | grep -q 12"
'

# Scenario 8: Help Flag Works
test_scenario "Help Flag (--help) Works" '
docker run --rm wfc-installer-test:latest bash -c "cd /wfc && ./install.sh --help 2>&1 | grep -q WFC"
'

# Scenario 9: Version Defined
test_scenario "Installer Version Defined" '
docker run --rm wfc-installer-test:latest bash -c "grep VERSION= /wfc/install-universal.sh | grep -q 0.6"
'

# Scenario 10: Skills Source Path Correct
test_scenario "Skills Source Path is wfc/skills" '
docker run --rm wfc-installer-test:latest bash -c "grep wfc/skills.*wfc- /wfc/install-universal.sh | grep -q wfc/skills"
'

echo "==================================="
echo "Test Suite Summary"
echo "==================================="
echo "Scenarios: $SCENARIO_COUNT"
echo -e "${GREEN}Passed:  $PASS_COUNT${RESET}"
echo -e "${RED}Failed:  $FAIL_COUNT${RESET}"
echo ""

if [ $FAIL_COUNT -eq 0 ]; then
    echo -e "${GREEN}${BOLD}🎉 ALL SCENARIOS PASSED!${RESET}"
    echo ""
    echo "The WFC installer is ready for release!"
    exit 0
else
    echo -e "${RED}${BOLD}⚠️  SOME SCENARIOS FAILED${RESET}"
    echo ""
    echo "Review the failures above and fix before release."
    exit 1
fi
