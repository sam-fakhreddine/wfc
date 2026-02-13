#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════════
# WFC CI Checks — runs inside the devcontainer image
#
# All tools (black, ruff, pytest, mypy, uv, pip) are pre-installed in the image.
# This script is the single source of truth for CI validation.
#
# Usage (from GitHub Actions):
#   docker run --rm --user root \
#     -v "$GITHUB_WORKSPACE:/workspace/app" \
#     wfc-devcontainer:ci \
#     bash /workspace/app/.devcontainer/scripts/ci-checks.sh
# ═══════════════════════════════════════════════════════════════════════════════
set -euo pipefail

cd /workspace/app

PASS=0
FAIL=0
WARN=0

step_pass() { PASS=$((PASS + 1)); echo "  ✓ $1"; }
step_fail() { FAIL=$((FAIL + 1)); echo "  ✗ $1"; }
step_warn() { WARN=$((WARN + 1)); echo "  ~ $1 (non-blocking)"; }

echo ""
echo "============================================"
echo "  WFC DevContainer CI"
echo "============================================"
echo ""

# ── Setup ──────────────────────────────────────────────────────────────────────
echo "▶ Setup"

# Mock Claude directory so install.sh detects a platform
mkdir -p ~/.claude/skills

pip install --root-user-action=ignore -e ".[dev,tokens]" --quiet 2>&1 | tail -1 || true
pip install --root-user-action=ignore build twine pyyaml --quiet 2>/dev/null || true

chmod +x install.sh
./install.sh --ci && step_pass "WFC skills installed" || step_fail "WFC skills install"
echo ""

# ── Code Quality ───────────────────────────────────────────────────────────────
echo "▶ Code Quality"

black --check --diff wfc/ && step_pass "black format" || step_fail "black format"
ruff check wfc/ && step_pass "ruff lint" || step_fail "ruff lint"
mypy wfc/ --ignore-missing-imports && step_pass "mypy types" || step_warn "mypy types"
echo ""

# ── Tests ──────────────────────────────────────────────────────────────────────
echo "▶ Tests"

pytest tests/ -v --tb=short && step_pass "test suite" || step_fail "test suite"
echo ""

# ── Persona Validation ────────────────────────────────────────────────────────
echo "▶ Persona Validation"

python3 << 'PERSONAS' && step_pass "persona library" || step_fail "persona library"
import json
from pathlib import Path

panels = Path("wfc/references/personas/panels")
errors = []
for f in sorted(panels.glob("*/*.json")):
    try:
        d = json.loads(f.read_text())
        missing = [k for k in ("id","name","panel","skills","lens","selection_criteria") if k not in d]
        if missing:
            errors.append(f"  {f.name}: missing {missing}")
        model = d.get("model_preference", {}).get("default", "")
        if model not in ("opus", "sonnet", "haiku"):
            errors.append(f"  {f.name}: invalid model '{model}'")
    except Exception as e:
        errors.append(f"  {f.name}: {e}")

if errors:
    print("\n".join(errors))
    raise SystemExit(1)
print(f"  {len(list(panels.glob('*/*.json')))} personas validated")
PERSONAS
echo ""

# ── Agent Skills Compliance ───────────────────────────────────────────────────
echo "▶ Agent Skills Compliance"

python3 << 'SKILLS' && step_pass "skills compliance" || step_fail "skills compliance"
import yaml, os, sys, xml.etree.ElementTree as ET

skills_dir = os.path.expanduser("~/.claude/skills")
failed = []
validated = 0
for entry in sorted(os.listdir(skills_dir)):
    if not entry.startswith("wfc-") or not os.path.isdir(os.path.join(skills_dir, entry)):
        continue
    path = os.path.join(skills_dir, entry, "SKILL.md")
    if not os.path.exists(path):
        failed.append(f"  {entry}: missing SKILL.md"); continue
    content = open(path).read()
    if not content.startswith("---"):
        failed.append(f"  {entry}: missing frontmatter"); continue
    parts = content.split("---", 2)
    if len(parts) < 3:
        failed.append(f"  {entry}: malformed frontmatter"); continue
    try:
        meta = yaml.safe_load(parts[1])
    except Exception as e:
        failed.append(f"  {entry}: bad YAML: {e}"); continue
    if not meta or not isinstance(meta, dict):
        failed.append(f"  {entry}: empty frontmatter"); continue
    miss = [k for k in ("name", "description") if k not in meta]
    if miss:
        failed.append(f"  {entry}: missing {miss}"); continue
    name = meta["name"]
    if name != name.lower() or " " in name:
        failed.append(f"  {entry}: bad name '{name}'"); continue
    if len(parts[2].strip()) < 50:
        failed.append(f"  {entry}: body too short"); continue
    validated += 1
if failed:
    print("\n".join(failed)); sys.exit(1)
print(f"  {validated} skills compliant")
SKILLS
echo ""

# ── Package Build ──────────────────────────────────────────────────────────────
echo "▶ Package Build"

python3 -m build 2>&1 | tail -3
twine check dist/* 2>&1 | tail -1
step_pass "package build + twine"
echo ""

# ── Install Verification ──────────────────────────────────────────────────────
echo "▶ Install Verification"

python3 << 'VERIFY' && step_pass "install verification" || step_fail "install verification"
import os, glob
sd = os.path.expanduser("~/.claude/skills")
skills = glob.glob(os.path.join(sd, "wfc-*"))
personas = glob.glob(os.path.join(sd, "wfc/references/personas/panels/*/*.json"))
assert len(skills) >= 10, f"Only {len(skills)} skills (need >=10)"
assert len(personas) >= 50, f"Only {len(personas)} personas (need >=50)"
print(f"  {len(skills)} skills, {len(personas)} personas")
VERIFY
echo ""

# ── Critical Imports ──────────────────────────────────────────────────────────
echo "▶ Critical Imports"

python3 -c "
from wfc.scripts.confidence_checker import ConfidenceChecker
from wfc.scripts.memory_manager import MemoryManager
from wfc.scripts.token_manager import TokenManager
from wfc.scripts.universal_quality_checker import UniversalQualityChecker
print('  All critical modules importable')
" && step_pass "critical imports" || step_fail "critical imports"
echo ""

# ── Token Benchmark ───────────────────────────────────────────────────────────
echo "▶ Token Benchmark"

python3 scripts/benchmark_tokens.py --compare 2>&1 | tail -5 \
    && step_pass "token benchmark" || step_warn "token benchmark"
echo ""

# ── Summary ────────────────────────────────────────────────────────────────────
echo "============================================"
echo "  Results: ${PASS} passed, ${FAIL} failed, ${WARN} warnings"
echo "============================================"

if [ "$FAIL" -gt 0 ]; then
    echo ""
    echo "CI FAILED"
    exit 1
fi

echo ""
echo "All CI checks passed"
