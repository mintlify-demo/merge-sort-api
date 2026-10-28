.PHONY: install run test

install:  ## create a venv and install dependencies
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

run:  ## start the API on http://localhost:8000
	.venv/bin/uvicorn main:app --reload

test:  ## run the test suite
	.venv/bin/python -m pytest -q

