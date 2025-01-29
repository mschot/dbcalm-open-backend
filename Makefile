SHELL := /bin/bash

.PHONY: setup
setup:
	source .venv/bin/activate && \
	python3 create_config_file.py

