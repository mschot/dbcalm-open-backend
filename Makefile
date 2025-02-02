SHELL := /bin/bash

.PHONY: setup
setup:
	source .venv/bin/activate && \
	python3 setup.py install --user

