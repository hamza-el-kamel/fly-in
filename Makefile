run:
	python3 -m main

install:
	pip install -r requirements.txt

debug:
	python3 -m pdb -m main

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	rm -rf .mypy_cache
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

lint:
	flake8 .
	mypy . --config-file=pyproject.toml --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	flake8 .
	mypy . --config-file=pyproject.toml --strict

.PHONY: install run debug clean lint lint-strict