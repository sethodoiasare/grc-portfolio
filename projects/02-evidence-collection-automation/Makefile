.PHONY: install demo demo-batch demo-list test test-cov api lint clean

install:
	python3 -m pip install -r requirements.txt

demo:
	@echo "=== ITGC Evidence Analyser Demo ==="
	python3 -m src.cli assess \
		--control IAM_001 \
		--evidence data/samples/sample_evidence_iam001.txt \
		--statement-type D \
		--output /tmp/itgc_demo.json \
		--pdf
	@echo ""
	python3 -m src.cli summary /tmp/itgc_demo.json

demo-batch:
	@echo "=== Batch Assessment Demo ==="
	python3 -m src.cli batch \
		--config data/samples/batch_config.yaml \
		--output-dir /tmp/itgc_batch_reports \
		--format both
	python3 -m src.cli summary /tmp/itgc_batch_reports/assessment_report.json

demo-list:
	python3 -m src.cli list-controls

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
