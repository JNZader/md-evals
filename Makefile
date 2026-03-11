.PHONY: help test test-parallel test-serial test-verbose test-benchmark test-coverage test-fast test-watch

# Default target
help:
	@echo "md-evals Test Commands (Phase 7: Parallel Execution)"
	@echo ""
	@echo "Serial Execution:"
	@echo "  make test              - Run all tests serially (baseline)"
	@echo "  make test-verbose      - Run with verbose output and short traceback"
	@echo ""
	@echo "Parallel Execution (Recommended):"
	@echo "  make test-parallel     - Run tests with 4 optimal workers (73% faster)"
	@echo "  make test-fast         - Run with auto-detected CPU workers"
	@echo ""
	@echo "Development:"
	@echo "  make test-benchmark    - Compare serial vs parallel performance"
	@echo "  make test-coverage     - Generate coverage reports (HTML + XML)"
	@echo "  make test-single FILE=test_file - Run specific test file"
	@echo ""
	@echo "Advanced:"
	@echo "  make test-loadscope    - Parallel with scope-based grouping"
	@echo "  make test-loadfile     - Parallel with file-based grouping"
	@echo "  make test-quick        - Run unit tests only (no integration/perf)"
	@echo ""

# Default test target (parallel with 4 workers)
test: test-parallel

# Serial execution (baseline for debugging)
test-serial:
	@echo "Running tests serially (baseline)..."
	python -m pytest tests/ -q --tb=short

# Parallel with 4 workers (optimal)
test-parallel:
	@echo "Running tests in parallel with 4 workers (73% faster)..."
	python -m pytest tests/ -n 4 -q --tb=short

# Auto-detect CPU cores
test-fast:
	@echo "Running tests with auto-detected workers..."
	python -m pytest tests/ -n auto -q --tb=short

# Verbose output
test-verbose:
	@echo "Running tests with verbose output..."
	python -m pytest tests/ -n 4 -v --tb=short

# Coverage reports (HTML + XML)
test-coverage:
	@echo "Running tests with coverage analysis..."
	python -m pytest tests/ -n 4 \
		--cov=md_evals \
		--cov-report=html:htmlcov \
		--cov-report=term-missing:skip-covered
	@echo "Coverage reports generated in htmlcov/"

# Benchmark: Serial vs Parallel
test-benchmark:
	@echo "=== Serial Execution ==="
	@time python -m pytest tests/ -q --tb=no
	@echo ""
	@echo "=== Parallel Execution (4 workers) ==="
	@time python -m pytest tests/ -n 4 -q --tb=no

# loadscope distribution (group by class/module)
test-loadscope:
	@echo "Running tests with loadscope distribution..."
	python -m pytest tests/ --dist=loadscope -n 4 -q --tb=short

# loadfile distribution (group by file)
test-loadfile:
	@echo "Running tests with loadfile distribution..."
	python -m pytest tests/ --dist=loadfile -n 4 -q --tb=short

# Quick test: unit tests only (skip performance/slow)
test-quick:
	@echo "Running quick unit tests only..."
	python -m pytest tests/ -n 4 -q --tb=short -m "not slow and not performance"

# Run specific test file
test-single:
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-single FILE=test_filename"; \
		exit 1; \
	fi
	@echo "Running $(FILE) in parallel..."
	python -m pytest tests/$(FILE) -n 4 -v --tb=short

# Performance tests only
test-perf:
	@echo "Running performance benchmark tests..."
	python -m pytest tests/test_performance.py -v --tb=short

# Specific test by pattern
test-match:
	@if [ -z "$(PATTERN)" ]; then \
		echo "Usage: make test-match PATTERN=test_pattern"; \
		exit 1; \
	fi
	@echo "Running tests matching: $(PATTERN)"
	python -m pytest tests/ -n 4 -k "$(PATTERN)" -v --tb=short

# Watch mode (requires pytest-watch)
test-watch:
	@command -v ptw >/dev/null 2>&1 || { \
		echo "pytest-watch not installed. Installing..."; \
		pip install pytest-watch; \
	}
	@echo "Watching tests for changes..."
	ptw tests/ -- -n 4 --tb=short

# CI mode (used in GitHub Actions)
test-ci:
	@echo "Running tests in CI mode (parallel, with coverage)..."
	python -m pytest tests/ -n 4 \
		--cov=md_evals \
		--cov-report=xml:coverage.xml \
		--cov-report=term-missing:skip-covered \
		--junitxml=test-results.xml

# Clean test artifacts
clean-test:
	@echo "Cleaning test artifacts..."
	rm -rf .pytest_cache htmlcov .coverage coverage.json coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Full test suite with all reports
test-all:
	@echo "Running full test suite with all reports..."
	python -m pytest tests/ -n 4 \
		--cov=md_evals \
		--cov-report=html:htmlcov \
		--cov-report=xml:coverage.xml \
		--cov-report=term-missing:skip-covered \
		--html=reports/test-report.html \
		--self-contained-html \
		-v --tb=short
	@echo ""
	@echo "Test Results:"
	@echo "  - Console output above"
	@echo "  - HTML coverage: htmlcov/index.html"
	@echo "  - HTML test report: reports/test-report.html"
	@echo "  - XML coverage: coverage.xml (for CI)"

.PHONY: clean-test
