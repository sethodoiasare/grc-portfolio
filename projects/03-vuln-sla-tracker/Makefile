.PHONY: install seed test api lint clean

install:
	pip install -r requirements.txt

seed:
	python -m src.seed_data

test:
	pytest tests/ -v --tb=short

api:
	uvicorn src.api:app --reload --port 8003

lint:
	ruff check src/ tests/ || true

clean:
	rm -rf __pycache__ .pytest_cache
