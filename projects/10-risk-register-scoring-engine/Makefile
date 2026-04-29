.PHONY: install test demo clean

install:
	python3 -m pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

demo:
	python3 -m src.cli demo
	@echo ""
	@echo "Demo complete. Export saved to data/demo-risk-register.json"

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -f data/*.json data/*.csv
