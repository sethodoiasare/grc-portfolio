.PHONY: install seed test api lint clean

install:
	python3 -m pip install -r requirements.txt

seed:
	python3 -m src.seed_data

test:
	pytest tests/ -v --tb=short

api:
	uvicorn src.api:app --reload --port 8003

lint:
	ruff check src/ tests/ || true

clean:
	rm -rf __pycache__ .pytest_cache
