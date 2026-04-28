.PHONY: install test demo clean

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

demo:
	python3 -m src.cli scan --demo --output data/classification-report.json

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -rf data/demo_scan
	rm -f data/*.json
