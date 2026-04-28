.PHONY: install test test-cov lint clean demo

install:
	python3 -m pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/ || true

demo:
	python3 -m src.cli \
		--all-from-dir data/sample_outputs \
		--project "GRC Demo Platform" \
		--branch "main" \
		--commit "abc123def456" \
		--pipeline-run "demo-run-001" \
		--audit-period "FY25-Q4" \
		--sign \
		--output evidence-package.json

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__ .pytest_cache .coverage htmlcov evidence-package.json
