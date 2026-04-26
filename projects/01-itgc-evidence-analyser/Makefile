.PHONY: install demo demo-batch demo-list test test-cov api lint clean

install:
	pip install -r requirements.txt

demo:
	@echo "=== ITGC Evidence Analyser Demo ==="
	python -m src.cli assess \
		--control IAM_001 \
		--evidence data/samples/sample_evidence_iam001.txt \
		--statement-type D \
		--output /tmp/itgc_demo.json \
		--pdf
	@echo ""
	python -m src.cli summary /tmp/itgc_demo.json

demo-batch:
	@echo "=== Batch Assessment Demo ==="
	python -m src.cli batch \
		--config data/samples/batch_config.yaml \
		--output-dir /tmp/itgc_batch_reports \
		--format both
	python -m src.cli summary /tmp/itgc_batch_reports/assessment_report.json

demo-list:
	python -m src.cli list-controls

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

api:
	uvicorn src.api:app --reload --port 8001

lint:
	ruff check src/ tests/ || true

clean:
	rm -rf /tmp/itgc_*.json /tmp/itgc_*.pdf /tmp/itgc_batch_reports __pycache__ .pytest_cache
