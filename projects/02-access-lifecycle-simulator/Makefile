.PHONY: install test demo clean

install:
	python3 -m pip install -r requirements.txt

test:
	python3 -m pytest tests/ -v --tb=short

demo:
	python3 -m src.cli scan --demo --output data/audit-report.json --cert-report --format both
	@echo "Report saved to data/audit-report.json and data/audit-report.pdf"

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -f data/*.json data/*.pdf data/samples/*.json
