.PHONY: install test demo demo-charts clean

install:
	pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

demo:
	python3 -m src.cli compute --demo --output data/metrics-report.json

demo-charts:
	python3 -m src.cli compute --demo --charts --chart-dir data/charts --output data/metrics-report.json

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -f data/*.json data/charts/*.png
