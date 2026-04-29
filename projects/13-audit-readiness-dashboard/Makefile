.PHONY: install test demo api clean

install:
	python3 -m pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

demo:
	@echo ""
	@echo "  ================================================"
	@echo "  Audit Readiness Dashboard — GRC Portfolio P13"
	@echo "  Starting server on http://localhost:8013"
	@echo "  Press Ctrl+C to stop"
	@echo "  ================================================"
	@echo ""
	python3 -m src.cli --port 8013

api:
	uvicorn src.api:app --reload --port 8013

clean:
	rm -rf __pycache__ .pytest_cache src/__pycache__ tests/__pycache__
	find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true
