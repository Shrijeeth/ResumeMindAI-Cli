format:
	python -m ruff format .

lint:
	python -m ruff check --select I,RUF022 --fix .

check:
	python -m ruff check .

install:
	python -m pip install -r requirements.txt

run:
	python main.py

clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

test:
	python -m pytest tests/ -v

dev-install:
	python -m pip install -r requirements.txt
	python -m pip install ruff pytest

.PHONY: format lint check install run clean test dev-install
