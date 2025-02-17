SHELL := /bin/bash

.PHONY: hooks

# Adds git hooks to the project
hooks:
	ln -s -f ../hooks .git/hooks


