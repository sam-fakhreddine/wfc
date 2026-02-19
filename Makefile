# WFC Makefile - World Fucking Class development tasks

.PHONY: help install test validate lint format clean check-all doctor \
		 act-pull act-check act-fast act-lint act-test act-validate pr

# Default target
help:
	@echo "WFC - World Fucking Class"
	@echo ""
	@echo "Available targets:"
	@echo "  make install         - Install WFC with all features"
	@echo "  make install-dev     - Install with dev dependencies"
	@echo "  make doctor          - Run comprehensive health checks"
	@echo "  make test            - Run all tests"
	@echo "  make validate        - Validate all WFC skills"
	@echo "  make lint            - Run linters (black + ruff)"
	@echo "  make format          - Format code (black)"
	@echo "  make check-all       - Run tests, validate, and lint"
	@echo "  make clean           - Remove build artifacts"
	@echo "  make pre-commit      - Install pre-commit hooks"
	@echo "  make benchmark       - Run token usage benchmarks"
	@echo ""
	@echo "act (Local CI) targets:"
	@echo "  make act-pull        - Pull act Docker images (first run, ~5-15 min)"
	@echo "  make act-check       - Full act CI gate (both workflows, ~10 min)"
	@echo "  make act-fast        - Fast mode: lint + validate only (~2 min)"
	@echo "  make act-lint        - Run only the lint job via act"
	@echo "  make act-test        - Run only the test job via act (ubuntu)"
	@echo "  make act-validate    - Run only validate.yml via act"
	@echo "  make pr              - Create PR (runs act gate first; bypass: WFC_SKIP_ACT=1 make pr)"

# Installation
install:
	@echo "🚀 Installing WFC with all features..."
	uv pip install -e ".[all]"
	@echo "✅ WFC installed"

install-dev:
	@echo "🔧 Installing WFC for development..."
	uv pip install -e ".[dev,tokens]"
	@echo "✅ Development environment ready"

# Testing
test:
	@echo "🧪 Running tests..."
	pytest -v
	@echo "✅ All tests passed"

test-coverage:
	@echo "📊 Running tests with coverage..."
	pytest --cov=wfc --cov-report=html --cov-report=term
	@echo "✅ Coverage report generated: htmlcov/index.html"

# Validation
validate:
	@echo "🔍 Validating all WFC skills..."
	@if [ ! -d "$(HOME)/repos/agentskills/skills-ref" ]; then \
		echo "❌ skills-ref not found at ~/repos/agentskills/skills-ref"; \
		exit 1; \
	fi
	@cd $(HOME)/repos/agentskills/skills-ref && \
	source .venv/bin/activate && \
	for skill in $(HOME)/.claude/skills/wfc-*; do \
		echo "  Validating $$(basename $$skill)..."; \
		if ! skills-ref validate "$$skill" > /dev/null 2>&1; then \
			echo "  ❌ $$(basename $$skill) failed"; \
			exit 1; \
		fi; \
		echo "  ✅ $$(basename $$skill)"; \
	done
	@echo "✅ All WFC skills validated"

validate-xml:
	@echo "🔍 Validating XML prompt generation..."
	@cd $(HOME)/repos/agentskills/skills-ref && \
	source .venv/bin/activate && \
	for skill in $(HOME)/.claude/skills/wfc-*; do \
		echo "  $$(basename $$skill)..."; \
		if ! skills-ref to-prompt "$$skill" | grep -q "<skill>"; then \
			echo "  ❌ XML generation failed"; \
			exit 1; \
		fi; \
	done
	@echo "✅ All XML prompts valid"

# Code quality
lint:
	@echo "🔍 Running linters..."
	uv run black --check wfc/ tests/ scripts/
	uv run ruff check wfc/
	@echo "✅ Lint passed"

format:
	@echo "🎨 Formatting code..."
	uv run black wfc/ tests/ scripts/
	uv run ruff check --fix wfc/
	@echo "✅ Code formatted"

format-check:
	@echo "🔍 Checking code format..."
	uv run black --check wfc/ tests/ scripts/
	uv run ruff check wfc/
	@echo "✅ Format is correct"

# Comprehensive checks
check-all: test validate lint
	@echo ""
	@echo "🎉 All checks passed!"
	@echo "  ✅ Tests"
	@echo "  ✅ Skill validation"
	@echo "  ✅ Linting"
	@echo ""
	@echo "This is World Fucking Class. 🚀"

# Pre-commit hooks
pre-commit:
	@echo "🪝 Installing pre-commit hooks..."
	@if [ ! -f .git/hooks/pre-commit ]; then \
		cp scripts/pre-commit.sh .git/hooks/pre-commit; \
		chmod +x .git/hooks/pre-commit; \
		echo "✅ Pre-commit hook installed"; \
	else \
		echo "⚠️  Pre-commit hook already exists"; \
	fi

# Health checks
doctor:
	@echo "🩺 Running WFC health checks..."
	@python3 scripts/doctor.py

# Benchmarks
benchmark:
	@echo "📊 Running token usage benchmarks..."
	@python3 scripts/benchmark_tokens.py
	@echo "✅ Benchmark complete"

benchmark-compare:
	@echo "📊 Comparing old vs new token usage..."
	@python3 scripts/benchmark_tokens.py --compare
	@echo "✅ Comparison complete"

# Quality Check (Pre-review gate) - UNIVERSAL with Trunk.io
quality-check:
	@echo "🔍 Running quality checks (Trunk.io)..."
	@trunk check || (echo "Install Trunk: curl https://get.trunk.io -fsSL | bash" && exit 1)
	@echo "✅ Quality check complete"

quality-check-fix:
	@echo "🔧 Running quality checks with auto-fix (Trunk)..."
	@trunk check --fix
	@echo "✅ All fixable issues fixed"

quality-check-python:
	@echo "🔍 Python-specific quality checks..."
	@python3 wfc/scripts/quality_checker.py $$(find wfc -name "*.py" -not -path "*/.venv/*")
	@echo "✅ Python checks complete"

# Cleanup
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf .pytest_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Clean"

# Development workflow
dev: install-dev pre-commit
	@echo "✅ Development environment ready"
	@echo ""
	@echo "Quick commands:"
	@echo "  make test         - Run tests"
	@echo "  make validate     - Validate skills"
	@echo "  make check-all    - Run all checks"


## ─── act (Local CI) ─────────────────────────────────────────────────────────

act-pull: ## Pull act Docker images (first run, ~5-15 min)
	@echo "📦 Pulling act Docker images (catthehacker/ubuntu:act-22.04)..."
	@act -W .github/workflows/ci.yml -j lint --pull=true --list

act-check: ## Run full act CI gate (both workflows, ~10 min after image pull)
	@bash scripts/act-check.sh

act-fast: ## Run act fast mode — lint + validate only (~2 min)
	@bash scripts/act-check.sh --fast

act-lint: ## Run only the lint job via act
	@act -W .github/workflows/ci.yml -j lint --pull=false

act-test: ## Run only the test job via act (ubuntu)
	@act -W .github/workflows/ci.yml -j test --matrix os:ubuntu-latest --pull=false

act-validate: ## Run only validate.yml via act
	@act -W .github/workflows/validate.yml --pull=false

pr: ## Create PR (runs act gate first; bypass: WFC_SKIP_ACT=1 make pr)
	@if [ "$(WFC_SKIP_ACT)" = "1" ]; then \
		echo "⚠  Skipping act gate (WFC_SKIP_ACT=1)"; \
	else \
		echo "▶  Running act gate before PR creation..."; \
		bash scripts/act-check.sh --fast || exit 1; \
	fi
	@gh pr create --fill

# CI simulation
ci: format-check test validate lint
	@echo "✅ CI checks passed"
