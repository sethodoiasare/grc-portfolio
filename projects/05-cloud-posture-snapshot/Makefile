.PHONY: install test test-cov lint demo demo-aws demo-all clean

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --tb=short --cov=src --cov-report=term-missing

lint:
	ruff check src/ tests/ || true

demo: demo-aws

demo-aws:
	python -m src.cli scan --provider aws --format both --output data/posture-report-aws.json

demo-azure:
	python -m src.cli scan --provider azure --format both --output data/posture-report-azure.json

demo-gcp:
	python -m src.cli scan --provider gcp --format both --output data/posture-report-gcp.json

demo-all:
	python -m src.cli scan --provider aws --format json --output data/posture-report-aws.json
	python -m src.cli scan --provider azure --format json --output data/posture-report-azure.json
	python -m src.cli scan --provider gcp --format json --output data/posture-report-gcp.json
	@echo "All three reports generated in data/"

list-aws:
	python -m src.cli list-checks --provider aws

list-azure:
	python -m src.cli list-checks --provider azure

list-gcp:
	python -m src.cli list-checks --provider gcp

clean:
	rm -rf __pycache__ src/__pycache__ src/checks/__pycache__ tests/__pycache__
	rm -rf .pytest_cache .coverage htmlcov
	rm -f data/*.json data/*.pdf
