.PHONY: install test demo clean

install:
	python3 -m pip install -r requirements.txt

test:
	pytest tests/ -v --tb=short

demo:
	python3 -m src.cli demo --format all
	@echo ""
	@echo "Demo complete. Exports saved to data/demo-risk-register.{json,csv,pdf}"

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -f data/*.json data/*.csv data/*.pdf
