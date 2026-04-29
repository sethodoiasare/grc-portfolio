.PHONY: install test demo clean

install:
	python3 -m pip install -r requirements.txt

test:
	python3 -m pytest tests/ -v --tb=short

demo:
	python3 -m src.cli generate --demo --output-dir data
	@echo "Demo runbooks saved to data/"

clean:
	rm -rf __pycache__ src/__pycache__ tests/__pycache__
	rm -rf .pytest_cache
	rm -f data/*.md data/*.json
