.PHONY: install test demo clean

install:
	python3 -m pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

demo:
	python3 -m src.cli score --demo --output data/demo-vendor-assessment.json --format both
	@echo "Reports saved to data/"

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -f data/*.json data/*.md
