.PHONY: test

test:
	poetry run pycodestyle .
	poetry run python -m unittest
