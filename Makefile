.PHONY: install test build publish

install:
	python -m pip install -e .[dev]

test:
	pytest -q

build:
	python -m build

publish:
	python -m twine upload dist/*
