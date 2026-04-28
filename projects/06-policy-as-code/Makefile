.PHONY: install test demo clean

install:
	python3 -m pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

demo:
	python3 -m src.cli scan --demo --output data/policy-report.json
	@echo "Report saved to data/policy-report.json"

clean:
	rm -rf __pycache__ src/__pycache__ src/policies/__pycache__ src/data/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -f data/*.json
